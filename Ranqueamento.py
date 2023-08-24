import base64
import requests
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt
from matplotlib import patches
import seaborn as sns

# Inicialize o estado da página se ainda não existir

if 'page' not in st.session_state:
    st.session_state.page = 0


@st.cache_data
def fetch_data(url, headers):
    """Busca os dados da API.
    :param url: URL da API
    :param headers: Cabeçalhos de autenticação
    :return: Conteúdo JSON se a resposta for bem-sucedida, código de status"""

    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        return response.json(), response.status_code
    return None, response.status_code



def process_data(data):
    """Processa os dados JSON e retorna um DataFrame.
    :param data: Dados em formato JSON
    :return: DataFrame processado"""
    rows = []
    for key, value in data.items():
        reserva = key
        corretor = value["corretor"]["corretor"]
        #Se o corretor for Evandro Rodrigues Da Silva, pule para a próxima iteração
        if corretor == 'Evandro Rodrigues da Silva':
            continue

        corretor_id = value ["corretor"]["idcorretor_cv"]
        empreendimento = value["unidade"]["empreendimento"]
        imobiliaria = value["corretor"]["imobiliaria"]  # Você pode escolher outro campo da imobiliária se preferir
        valor_contrato = value["condicoes"]["valor_contrato"]
        data_venda = value["data_venda"]
        row = {
            'reserva': reserva,
            "empreendimento": empreendimento,
            "corretor": corretor,
            "id_corretor": corretor_id,
            "imobiliaria": imobiliaria,
            "valor_contrato": valor_contrato,
            "data_venda": data_venda,
        }
        rows.append(row)

    return pd.DataFrame(rows)


def calcular_total_vendas(df):
    return df['valor_contrato'].sum()

def normalizar_nome(nome):
    return ' '.join([word.capitalize() for word in nome.split()])

def diminuir_name(name, max_length = 45):
    if len(name) <= max_length:
        return name

    parts = name.split()
    for i in range(1, len(parts) - 1):
        # Substitua os nomes do meio por sua primeira letra e um ponto
        if len(name) > max_length:
            parts[i] = parts[i][0] + '.'
            name = ' '.join(parts)

    return name


def filter_by_empreendimento(df, empreendimento):
    if empreendimento == "BE GARDEN":
        return df[df['empreendimento'] == 'BE GARDEN KAÁ SQUARE']        
    elif empreendimento != 'TOTAL':
        return df[df['empreendimento'] == empreendimento]     
    return df

def processar_name(name):
    normalized_name = normalizar_nome(name)
    shortened_name = diminuir_name(normalized_name)
    return shortened_name


def prepare_data(df):
    """Prepara os dados para o gráfico.

    :param df: DataFrame contendo os dados
    :return: ranking, cores"""

    # Filtra por empreendimento, se aplicável
    empreendimento = st.session_state.get('empreendimento', 'TOTAL')
    df = filter_by_empreendimento(df, empreendimento)

    # Agrupar e ordenar os dados
    ranking = df.groupby(['corretor'], as_index=False)['valor_contrato'].sum()    
    ranking = ranking.sort_values(by='valor_contrato', ascending=False)

    # Normalizar os nomes
    ranking['corretor'] = ranking['corretor'].apply(processar_name)
    
    # Definir as cores
    first_color = '#007c83'
    others_color = '#9c9fae'

    colors = [first_color] + [others_color] * (len(ranking) - 1)
    # Usar todas as cores base e adicionar cores aleatórias, se necessário
    #colors = base_colors[:len(ranking)] + random_colors
    return ranking, colors, empreendimento

def calcular_primeiro_lugar(df):
    ranking, _, empreendimento = prepare_data(df)
    if len(ranking) > 0:
        primeiro_lugar = ranking.iloc[0]['corretor']
        return primeiro_lugar, empreendimento
    return None, None

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
    fig, ax = plt.subplots(figsize=(12, 10))

    # tornar o fundo transparente
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    propriedades = [
    {'color': '#007c83', 'fontsize': 25, 'weight': 'bold'},  # Primeiro colocado
    {'color': '#9c9fae', 'fontsize': 22, 'weight': 'bold'},  # Segundo colocado
    {'color': '#9c9fae', 'fontsize': 20, 'weight': 'bold'},  # Terceiro colocado
]


    # Criar o gráfico
    sns.barplot(x='valor_contrato', y='corretor', data=subset_ranking, palette=subset_colors)
    valor_maximo = subset_ranking['valor_contrato'].max()

    # Remova os rótulos padrão do eixo Y
    ax.set_yticks(range(len(subset_ranking['corretor'])))
    ax.set_yticklabels([])

    # Adicionar rótulos manualmente, destacando o primeiro
    for  idx, corretor in enumerate(subset_ranking['corretor']):
        if st.session_state.page == 0 and idx == 0:
            props = propriedades[0]
        else:
            props = propriedades[1]
            #ajusta a pos dos nomes
        posicao_x = -0.02 * valor_maximo
        ax.text(posicao_x, idx, corretor, ha='right', va='center', **props)

    # Se estiver na primeira página, destacar o primeiro corretor
    if st.session_state.page == 0:
        valor_primeiro = subset_ranking['valor_contrato'].iloc[0]

        # Colocar a palavra "Líder" no meio da barra do primeiro colocado
        ax.text(valor_primeiro / 2, 0, 'BEst Seller', ha='center', va='center', color='black', fontsize = 25)

        # Adicionar uma borda ao redor da barra do primeiro colocado
        rect = patches.Rectangle((0, -0.4), valor_primeiro, 0.8, linewidth=4, edgecolor='black', facecolor='none')
        ax.add_patch(rect)

    plt.xlabel('')
    plt.ylabel('Corretores')
    ax.yaxis.set_label_coords(0,0)
    ax.yaxis.get_label().set_text('')
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

    if st.session_state.page == 0:
        ax.yaxis.get_ticklabels()[0].set_fontsize(15)

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

    ranking, colors, _ = prepare_data(df)
    if len(ranking) == 0:
        st.write("Não existem vendas cadastradas para este empreendimento.")
        return
    subset_ranking, subset_colors = select_data(ranking, colors)
    fig, ax = create_plot(subset_ranking, subset_colors)
    customize_plot(fig, ax, ranking)

    # Botões abaixo do gráfico
    display_page_buttons(ranking)

def create_meta_plot(total_vendas, metas):
    fig, ax = plt.subplots(figsize=(10, 4))


    # tornar o fundo transparente
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)

    # Cores para diferentes faixas de progresso
    if total_vendas < metas[0]:
        bar_color = 'red'
    elif total_vendas < metas[1]:
        bar_color = 'yellow'
    else:
        bar_color = 'green'

    plt.barh(['Total Vendas'], total_vendas, color=bar_color)
    
    # Linhas de Meta (sempre visíveis)
    plt.axvline(x=metas[0], color='#9c9fae', linestyle='--', linewidth=3, label='Meta 30M')
    plt.axvline(x=metas[1], color='#007c83', linestyle='--', linewidth=3, label='Meta 60M')
    
    # Limites do eixo x para sempre mostrar as metas
    plt.xlim(0, max(metas[1], total_vendas) * 1.1)

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
    #st.write(legend.get_texts())
    # for text in legend.get_texts():
    #     text.set_color("#9c9fae")

    st.pyplot(fig)

def display_meta_vendas(total_vendas):
    """Exibe o progresso em relação às metas no Streamlit.

    :param total_vendas: Total de vendas """

    metas = [30000000, 60000000]
    fig, ax = create_meta_plot(total_vendas, metas)
    customize_meta_plot(fig, ax)

def display_empreendimento_buttons(df):
    
    empreendimentos = [ 'TOTAL','BE GARDEN', 'BE BONIFÁCIO', 'BE DEODORO']
    cols = st.columns(len(empreendimentos))
    for i, empreendimento in enumerate(empreendimentos):
        if cols[i].button(empreendimento):  # Colocar cada botão em sua própria coluna
            st.session_state.empreendimento = empreendimento
            st.session_state.page = 0
            st.experimental_rerun()

@st.cache_data
def get_base64_of_bin_file(bin_file):
    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    bin_str = get_base64_of_bin_file(png_file)
    page_bg_img = '''
    <style>
    .stApp {
        background-image: url("data:image/png;base64,%s");
        background-size: cover;
    }
    </style>
    ''' % bin_str
    
    st.markdown(page_bg_img, unsafe_allow_html=True)


def exibir_graficos(df):

    total_vendas = df['valor_contrato'].sum()
    set_png_as_page_bg('Imagens/white-background.jpeg')

    # Você pode adicionar um cabeçalho
    col1, col2 = st.columns([0.25, 4])
    with col1:
        st.image('Imagens/be-monocromia-cinza.png', use_column_width = True)
    # Coluna 1: Imagem
    with col2:
        st.markdown("<div style='text-align: center;'><span style='color: black; font-size:30px; font-weight:bold;'>BE Corretor Premiado</span></div>", unsafe_allow_html=True)
    primeiro_lugar, empreendimento = calcular_primeiro_lugar(df)

    if primeiro_lugar is not None and  empreendimento == 'TOTAL':
        st.markdown(f"<p style='text-align: center; color: black; font-size:30px; font-weight:bold;'>🏆 O <span style='color: #007c83;'>BE</span>st Seller atual é <span style='color: #007c83;'>{primeiro_lugar}</span>!</p>", unsafe_allow_html=True)
    if primeiro_lugar is None:
        st.write("Nao existe ranking atual deste empreendimento!")


    display_empreendimento_buttons(df)

    display_corretor_ranking(df)

    # Mostrar o progresso em relação às metas
    display_meta_vendas(total_vendas)

    # Você pode adicionar um rodapé
    st.markdown("© BravoEA - [Website](http://www.serbravo.com.br)")
    st.markdown("---")


def main():
    st.set_page_config(
        page_title="BE Corretor Premiado",
        initial_sidebar_state="collapsed",
)
    url = st.secrets['User_url']
    headers = {
        "email": st.secrets['User_email'], 
        "token": st.secrets['User_token']
    }

    data_reserva,status = fetch_data(url,headers)


    if data_reserva:
        df_reserva_filtrado = (process_data(data_reserva)
                              .astype({'id_corretor': int, 'valor_contrato': float})
                              .assign(data_venda=lambda x: pd.to_datetime(x['data_venda']))
                              .query('data_venda > "2022-01-01"'))
        
        exibir_graficos(df_reserva_filtrado)
    else:
        st.write(f"A operação falhou, com status {status}")


if __name__ == '__main__':
    main()