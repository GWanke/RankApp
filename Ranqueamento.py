import requests
import pandas as pd
import json
import streamlit as st
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import seaborn as sns
import numpy as np

# Inicialize o estado da página se ainda não existir
if 'page' not in st.session_state:
    st.session_state.page = 0

def fetch_data(url, headers):
    """Busca os dados da API.
    :param url: URL da API
    :param headers: Cabeçalhos de autenticação
    :return: Conteúdo JSON se a resposta for bem-sucedida, caso contrário None"""
    
    response = requests.get(url, headers=headers)
    return response.json() if response.status_code == 200 else None

def save_cache(data, cache_file='response_cache.json'):
    """Salva os dados em um arquivo JSON.
    :param data: Dados para salvar
    :param cache_file: Nome do arquivo de cache (opcional)"""

    with open(cache_file, 'w') as file:
        json.dump(data, file)

def load_cache(cache_file='response_cache.json'):
    """Carrega os dados de um arquivo JSON.
    :param cache_file: Nome do arquivo de cache (opcional)
    :return: Dados carregados"""

    with open(cache_file, 'r') as file:
        return json.load(file)

def process_data(data):
    """Processa os dados JSON e retorna um DataFrame.
    :param data: Dados em formato JSON
    :return: DataFrame processado"""
    rows = []
    empr_unicos = set()
    for key, value in data.items():
        corretor = value["corretor"]["corretor"]
        #Se o corretor for Evandro Rodrigues Da Silva, pule para a próxima iteração
        if corretor == 'Evandro Rodrigues da Silva':
            continue
        empreendimento = value["unidade"]["empreendimento"]
        empr_unicos.add(empreendimento)
        imobiliaria = value["corretor"]["imobiliaria"]  # Você pode escolher outro campo da imobiliária se preferir
        valor_contrato = value["condicoes"]["valor_contrato"]
        data_venda = value["data_venda"]

        row = {
            "empreendimento": empreendimento,
            "corretor": corretor,
            "imobiliaria": imobiliaria,
            "valor_contrato": valor_contrato,
            "data_venda": data_venda,
        }
        rows.append(row)
    print(list(empr_unicos))
    return pd.DataFrame(rows)

def calcular_total_vendas(df):
    return df['valor_contrato'].sum()

def normalizar_nome(nome):
    return ' '.join([word.capitalize() for word in nome.split()]) 

def filter_by_empreendimento(df, empreendimento):
    if empreendimento != "Total":
        return df[df['empreendimento'] == empreendimento]
    return df


def prepare_data(df):
    """Prepara os dados para o gráfico.

    :param df: DataFrame contendo os dados
    :return: ranking, cores"""

    # Filtra por empreendimento, se aplicável
    empreendimento = st.session_state.get('empreendimento', 'Total')
    df = filter_by_empreendimento(df, empreendimento)

    # Agrupar e ordenar os dados
    ranking = df.groupby('corretor')['valor_contrato'].sum().reset_index()
    ranking = ranking.sort_values(by='valor_contrato', ascending=False)

    # Normalizar os nomes
    ranking['corretor'] = ranking['corretor'].apply(normalizar_nome)
    
    # Definir as cores
    colors = ['gold', 'silver', 'brown'] + [mcolors.CSS4_COLORS[name] for name in np.random.choice(list(mcolors.CSS4_COLORS), len(ranking) - 3)]

    return ranking, colors


def select_data(ranking, colors):
    """Seleciona os dados usando o controle deslizante.

    :param ranking: DataFrame com os dados classificados
    :param colors: Lista de cores
    :return: subset_ranking, subset_colors"""

    items_per_page = 10

    # Calcule o índice inicial com base na página atual
    start_index = st.session_state.page * items_per_page

    # Filtrar os dados com base na seleção
    subset_ranking = ranking[start_index:start_index + items_per_page]

    # Definir as cores para o subconjunto atual
    subset_colors = colors[start_index:start_index + items_per_page]

    return subset_ranking, subset_colors




def create_plot(subset_ranking, subset_colors):
    """Cria o gráfico.

    :param subset_ranking: DataFrame com os dados selecionados
    :param subset_colors: Lista de cores selecionadas
    :return: fig, ax """
        
    # Criar o gráfico
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(x='valor_contrato', y='corretor', data=subset_ranking,palette = subset_colors )
    plt.xlabel('')
    plt.ylabel('Corretor')
    plt.title('Ranking dos Corretores')

    return fig, ax

def customize_plot(fig, ax, ranking):
    """Personaliza o gráfico.

    :param fig: Figura do gráfico
    :param ax: Eixo do gráfico
    :param ranking: DataFrame com os dados classificados """

    # Definir o fundo do gráfico para preto
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')

    # Definir as cores das etiquetas dos eixos, título e ticks para branco
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    ax.tick_params(axis='both', colors='white')

    
    # Definir o limite x para o valor de contrato mais alto no conjunto de dados completo
    ax.set_xlim(0, ranking['valor_contrato'].max())

    # Remover a legenda do eixo x para ocultar os valores de 'valor_contrato'
    ax.set(xticklabels=[])

    # Exibir o gráfico no Streamlit
    st.pyplot(fig)

def display_page_buttons(ranking):
    items_per_page = 10
    total_pages = (len(ranking) + items_per_page - 1) // items_per_page

    button_clicked = False

    col1, _, col2 = st.columns([1, 3, 1]) # Ajuste os números para alterar o espaçamento

    # Desabilite o botão 'Anterior' na primeira página
    if col1.button('Anterior', key='anterior', disabled=(st.session_state.page == 0)):
        st.session_state.page -= 1
        button_clicked = True

    # Desabilite o botão 'Próximo' na última página
    if col2.button('Próximo', key='proximo', disabled=(st.session_state.page == total_pages - 1)):
        st.session_state.page += 1
        button_clicked = True

    if button_clicked:
        st.experimental_rerun()
  

def display_corretor_ranking(df):
    """Agrupa a soma dos valor_contrato por corretor e exibe no Streamlit.

    :param df: DataFrame contendo os dados """

    ranking, colors = prepare_data(df)
    subset_ranking, subset_colors = select_data(ranking, colors)
    fig, ax = create_plot(subset_ranking, subset_colors)
    customize_plot(fig, ax, ranking)

    # Botões abaixo do gráfico
    display_page_buttons(ranking)

def create_meta_plot(total_vendas, metas):
    """Cria o gráfico de meta de vendas.

    :param total_vendas: Total de vendas
    :param metas: Lista das metas
    :return: fig, ax """
    
    fig, ax = plt.subplots(figsize=(10, 2))

    plt.barh(['Total Vendas'], total_vendas, color='green')
    plt.axvline(x=metas[0], color='blue', linestyle='--', label='Meta 30M')
    plt.axvline(x=metas[1], color='red', linestyle='--', label='Meta 60M')

    return fig, ax

def customize_meta_plot(fig, ax):
    """Personaliza o gráfico de meta de vendas.

    :param fig: Figura do gráfico
    :param ax: Eixo do gráfico """

    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.tick_params(axis='both', colors='white')
    ax.set(xticklabels=[])

    plt.xlabel('')
    plt.ylabel('')
    plt.title('Progresso das Metas', color='white')

    legend = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
    for text in legend.get_texts():
        text.set_color("white")

    st.pyplot(fig)

def display_meta_vendas(total_vendas):
    """Exibe o progresso em relação às metas no Streamlit.

    :param total_vendas: Total de vendas """

    metas = [30000000, 60000000]
    fig, ax = create_meta_plot(total_vendas, metas)
    customize_meta_plot(fig, ax)

def display_empreendimento_buttons(df):
    empreendimentos = ['BE GARDEN KAÁ SQUARE', 'BE BONIFÁCIO', 'BE DEODORO', 'Total']
    cols = st.columns(len(empreendimentos))
    for i, empreendimento in enumerate(empreendimentos):
        if cols[i].button(empreendimento):  # Colocar cada botão em sua própria coluna
            st.session_state.empreendimento = empreendimento
            st.experimental_rerun()


def exibir_graficos(df):
    
    total_vendas = df['valor_contrato'].sum()

    display_empreendimento_buttons(df)
    # Mostrar o ranking dos corretores
    display_corretor_ranking(df)

    # Mostrar o progresso em relação às metas
    display_meta_vendas(total_vendas)


def main():
    cache_file = 'response_cache.json'

    if os.path.exists(cache_file):
        # Carregar os dados do arquivo de cache
        data = load_cache(cache_file)
    else:
        # Buscar os dados da API
        url = st.secrets['User_url']
        headers = {
            "email": st.secrets[User_email], 
            "token": st.secrets[User_token]
        }
        
        data = fetch_data(url, headers)
        if data:
            # Salvar a resposta no arquivo de cache
            save_cache(data, cache_file)
        else:
            st.write(f"Erro ao consumir a API: {response.status_code}")
            return

    df = process_data(data)
    # Converter a coluna valor_contrato para float
    df['valor_contrato'] = df['valor_contrato'].astype(float)
    # Converter a coluna data_venda para datetime
    df['data_venda'] = pd.to_datetime(df['data_venda'])
    exibir_graficos(df)


if __name__ == '__main__':
    main()
