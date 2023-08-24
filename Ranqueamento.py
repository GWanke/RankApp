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

cores_empr = {
    "BE GARDEN": {"Principal": "#2B3956", "Secundária": "#9FCC2E"},
    "BE DEODORO": {"Principal": "#EA580C", "Secundária": "#F6A200"},
    "BE BONIFÁCIO": {"Principal": "#36261C", "Secundária": "#D19A53"},
    "TOTAL": {"Principal": "#007c83", "Secundária": "#9c9fae"},
}


@st.cache_data
def fetch_data(url, headers):
    """Busca os dados da API.
    :param url: URL da API como string.
    :param headers: Dicionário contendo os cabeçalhos de autenticação.
    :return: Tupla contendo o conteúdo JSON se a resposta for bem-sucedida e o código de status da resposta."""

    response = requests.get(url, headers=headers, timeout = 90)
    if response.status_code == 200:
        return response.json(), response.status_code
    return None, response.status_code



def process_data(data):
    """Processa os dados JSON e retorna um DataFrame.
    :param data: Dados em formato JSON como dicionário.
    :return: DataFrame processado com os dados."""

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
    """Calcula o valor total de vendas no DataFrame fornecido.
    :param df: DataFrame contendo os dados de vendas.
    :return: Valor total das vendas como float."""
    return df['valor_contrato'].sum()

def normalizar_nome(nome):
    """Normaliza o nome, capitalizando cada palavra.
    :param nome: Nome como string.
    :return: Nome normalizado como string."""
    return ' '.join([word.capitalize() for word in nome.split()])

def diminuir_name(name, max_length = 30):
    """Diminui o nome para um comprimento máximo, abreviando os nomes do meio.
    :param name: Nome completo como string.
    :param max_length: Comprimento máximo permitido para o nome.
    :return: Nome abreviado como string."""

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
    """Filtra o DataFrame por empreendimento.
    :param df: DataFrame contendo os dados.
    :param empreendimento: Nome do empreendimento como string.
    :return: DataFrame filtrado com base no empreendimento."""
    
    if empreendimento == "BE GARDEN":
        return df[df['empreendimento'] == 'BE GARDEN KAÁ SQUARE']        
    if empreendimento != 'TOTAL':
        return df[df['empreendimento'] == empreendimento]     
    return df

def processar_name(name):
    """Processa o nome, normalizando e diminuindo conforme necessário.
    :param name: Nome como string.
    :return: Nome processado como string."""

    normalized_name = normalizar_nome(name)
    shortened_name = diminuir_name(normalized_name)
    return shortened_name


def prepare_data(df):
    """
    Prepara os dados para o ranking, incluindo a filtragem por empreendimento e cores associadas.

    :param df: DataFrame contendo os dados
    :return: ranking, colors, empreendimento
    """
    empreendimento = st.session_state.get('empreendimento', 'TOTAL')

    df = filter_by_empreendimento(df, empreendimento)
    first_color = cores_empr[empreendimento]["Principal"]
    others_color = cores_empr[empreendimento]["Secundária"]

    ranking = df.groupby(['corretor'], as_index=False)['valor_contrato'].sum()
    ranking = ranking.sort_values(by='valor_contrato', ascending=False)
    ranking['corretor'] = ranking['corretor'].apply(processar_name)

    colors = [first_color] + [others_color] * (len(ranking) - 1)

    return ranking, colors, empreendimento

def calcular_primeiro_lugar(df):
    """
    Calcula o primeiro lugar no ranking.

    :param df: DataFrame contendo os dados
    :return: nome do corretor em primeiro lugar e empreendimento
    """
    ranking, _, empreendimento = prepare_data(df)
    if len(ranking) > 0:
        primeiro_lugar = ranking.iloc[0]['corretor']
        return primeiro_lugar, empreendimento
    return None, None

def select_data(ranking, colors):
    """
    Seleciona os dados para a página atual do ranking.

    :param ranking: DataFrame contendo o ranking
    :param colors: lista de cores
    :return: subset_ranking, subset_colors
    """
    items_per_page = 10
    start_index = st.session_state.page * items_per_page
    subset_ranking = ranking[start_index:start_index + items_per_page]
    subset_colors = colors[start_index:start_index + items_per_page]

    return subset_ranking, subset_colors

def create_and_customize_plot(subset_ranking, subset_colors, cor_prim, cor_secund, ranking):
    """
    Cria e personaliza o gráfico de barras para o ranking.

    :param subset_ranking: DataFrame contendo o subset do ranking
    :param subset_colors: lista de cores para o subset
    :param cor_prim: cor principal
    :param cor_secund: cor secundária
    :param ranking: DataFrame contendo o ranking completo
    """
    fig, ax = plt.subplots(figsize=(12, 10))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    sns.barplot(x='valor_contrato', y='corretor', data=subset_ranking, palette=subset_colors)
    valor_maximo = subset_ranking['valor_contrato'].max()
    ax.set_yticks(range(len(subset_ranking['corretor'])))
    ax.set_yticklabels([])

    for idx, corretor in enumerate(subset_ranking['corretor']):
        props = {'fontsize': 20, 'weight': 'bold'}
        if st.session_state.page == 0 and idx == 0:
            props['color'] = cor_prim
            props['fontsize'] = 25
        else:
            props['color'] = cor_secund
            props['fontsize'] = 22
        posicao_x = -0.02 * valor_maximo
        ax.text(posicao_x, idx, corretor, ha='right', va='center', **props)

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

    # Personalização
    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.xaxis.label.set_color('white')
    ax.yaxis.label.set_color('white')
    ax.title.set_color('white')
    ax.tick_params(axis='both', colors='white')
    ax.set_xlim(0, ranking['valor_contrato'].max())
    ax.set(xticklabels=[])
    if st.session_state.page == 0:
        ax.yaxis.get_ticklabels()[0].set_fontsize(15)

    st.pyplot(fig)

def display_page_buttons(ranking):
    """
    Cria e personaliza o gráfico de barras para o ranking.

    :param subset_ranking: DataFrame contendo o subset do ranking
    :param subset_colors: lista de cores para o subset
    :param cor_prim: cor principal
    :param cor_secund: cor secundária
    :param ranking: DataFrame contendo o ranking completo
    """
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
    """
    Exibe o ranking dos corretores na interface.

    :param df: DataFrame contendo os dados"""

    ranking, colors, empreendimento = prepare_data(df)
    cor_prim = cores_empr[empreendimento]['Principal']
    cor_secund = cores_empr[empreendimento]['Secundária']

    if len(ranking) == 0:
        st.write("")
        return

    subset_ranking, subset_colors = select_data(ranking, colors)
    create_and_customize_plot(subset_ranking, subset_colors, cor_prim, cor_secund, ranking)
    display_page_buttons(ranking)

def create_meta_plot(total_vendas, metas):
    """
    Cria um gráfico de barra horizontal mostrando o progresso em relação às metas.

    :param total_vendas: Total de vendas alcançado
    :param metas: Lista contendo as metas
    :return: fig, ax - Figura e eixo do gráfico"""
    
    fig, ax = plt.subplots(figsize=(10, 4))
    fig.patch.set_alpha(0)
    ax.patch.set_alpha(0)
    
    # Cores para diferentes faixas de progresso
    bar_color = 'green' if total_vendas >= metas[1] else 'yellow' if total_vendas >= metas[0] else 'red'
    plt.barh(['Total Vendas'], total_vendas, color=bar_color)
    
    # Linhas de Meta (sempre visíveis)
    for i, meta in enumerate(metas):
        label = f'Meta {30 * (i + 1)}M'
        plt.axvline(x=meta, color='#9c9fae' if i == 0 else '#007c83', linestyle='--', linewidth=3, label=label)
    
    plt.xlim(0, max(metas[1], total_vendas) * 1.1)

    return fig, ax

def customize_meta_plot(fig, ax):
    """
    Personaliza o gráfico de meta de vendas.

    :param fig: Figura do gráfico
    :param ax: Eixo do gráfico"""

    fig.patch.set_facecolor('black')
    ax.set_facecolor('black')
    ax.tick_params(axis='both', colors='white')
    ax.set(xticklabels=[])
    plt.xlabel('')
    plt.ylabel('')
    plt.title('Progresso das Metas', color='white')
    a = plt.legend(loc='center left', bbox_to_anchor=(1, 0.5), frameon=False)
    st.pyplot(fig)

def display_meta_vendas(total_vendas):
    """
    Exibe o progresso em relação às metas no Streamlit.

    :param total_vendas: Total de vendas"""

    metas = [30000000, 60000000]
    fig, ax = create_meta_plot(total_vendas, metas)
    customize_meta_plot(fig, ax)

def display_empreendimento_buttons():
    """
    Exibe os botões de empreendimento no Streamlit.

    :param df: DataFrame contendo os dados"""
    
    empreendimentos = ['TOTAL', 'BE GARDEN', 'BE BONIFÁCIO', 'BE DEODORO']
    cols = st.columns(len(empreendimentos))
    for i, empreendimento in enumerate(empreendimentos):
        if cols[i].button(empreendimento):
            st.session_state.empreendimento = empreendimento
            st.session_state.page = 0
            st.experimental_rerun()

@st.cache_data
def get_base64_of_bin_file(bin_file):
    """
    Converte um arquivo binário para sua representação em base64.

    :param bin_file: Caminho para o arquivo binário
    :return: string - Representação em base64 do arquivo binário"""

    with open(bin_file, 'rb') as f:
        data = f.read()
    return base64.b64encode(data).decode()

def set_png_as_page_bg(png_file):
    """
    Define uma imagem PNG como plano de fundo da página.

    :param png_file: Caminho para o arquivo PNG"""

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

def mensagem(primeiro_lugar, empreendimento):
    """
    Gera uma mensagem formatada anunciando o primeiro lugar em vendas para um empreendimento específico.

    :param primeiro_lugar: Nome do corretor em primeiro lugar
    :param empreendimento: Nome do empreendimento
    :return: string - Mensagem HTML formatada
    """

    if primeiro_lugar is None or empreendimento is None:
        return "<p style='text-align: center; color: black; font-size:25px; font-weight:bold;'>Não existe ranking atual deste empreendimento!</p>"

    cor_prim = cores_empr[empreendimento]['Principal']
    cor_secund = cores_empr[empreendimento]['Secundária']
    
    message = f"<p style='text-align: center; color: black; font-size:30px; font-weight:bold;'>🏆 O <span style='color: {cor_prim};'>BE</span>st Seller atual"

    if empreendimento != 'TOTAL':
        message += f" do <span style='color: {cor_secund};'>{empreendimento}</span>"

    message += f" é <span style='color: {cor_prim};'>{primeiro_lugar}</span>!</p>"

    return message


def exibir_graficos(df):
    """
    Exibe os gráficos de vendas e progresso em relação às metas no Streamlit.

    :param df: DataFrame contendo os dados de vendas
    """

    hide_img_fs = '''
    <style>
    button[title="View fullscreen"]{
        visibility: hidden;}
    </style>
    '''

    st.markdown(hide_img_fs, unsafe_allow_html=True)

    total_vendas = df['valor_contrato'].sum()
    set_png_as_page_bg('Imagens/white-background.jpeg')

    # Você pode adicionar um cabeçalho
    primeiro_lugar, empreendimento = calcular_primeiro_lugar(df)

    st.markdown(mensagem(primeiro_lugar, empreendimento), unsafe_allow_html=True)

    display_empreendimento_buttons()

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
                              .query('data_venda > "2023-01-01"'))
        
        exibir_graficos(df_reserva_filtrado)
    else:
        if status == 504:
            mensagem_erro = "Desculpe, estamos enfrentando um atraso na resposta do servidor. Por favor, tente novamente mais tarde. Se o problema persistir, entre em contato com a nossa equipe de suporte em: gustavo.w@bravoea.com"
        elif status == 429:
            mensagem_erro = "Parece que houve muitas solicitações em um curto período de tempo. Por favor, aguarde alguns minutos e tente novamente."
        else:
            mensagem_erro = f"Ocorreu um erro inesperado com o código de status {status}. Se você continuar enfrentando esse problema, por favor, entre em contato com nossa equipe de suporte em: gustavo.w@bravoea.com"

        st.write(mensagem_erro)



if __name__ == '__main__':
    main()
