import streamlit as st
import requests 
import pandas as pd
import plotly.express as px
from urllib.request import urlopen, urlretrieve, Request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup
from prophet import Prophet
import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import plotly.graph_objects as go
from pandas.plotting import autocorrelation_plot
import time




st.set_page_config(layout='wide')

# funcoes
def formata_numero(valor):
    return f'{valor:.2f}'    
   
# manter o cache do arquivo em memoria
@st.cache_data
def converte_csv(df):
   return df.to_csv(index = False).encode('utf-8')

def mensagem_sucesso():
   sucesso = st.success('Arquivo baixado com sucesso', icon = "✅")
   time.sleep(5)
   sucesso.empty()


st.title('Dados Estatísticos - Séries Temporais')


st.sidebar.title('Filtros')



# obtendo o html
url = 'http://www.ipeadata.gov.br/ExibeSerie.aspx?module=m&serid=1650971490&oper=view'
headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64, x64)"}

req = Request(url, headers=headers)
response = urlopen(req)
html = response.read()
soup = BeautifulSoup(html, 'html.parser')

# extraindo os dados da tabela
tabela = soup.find('table', id='grd_DXMainTable')

# extraindo os dados das linhas da tabela
colunas = tabela.find_all('td', class_='dxgv')

# criando listas para armazenar data e valor
lista_data = []
lista_valor = []

for coluna in colunas:
    texto = str(coluna.getText())
    if (',' not in texto):
      lista_data.append(texto)
    else:
      lista_valor.append(texto)

# criando um dicionario de dados para armazenar os dados extraídos nas listas criadas
dic_valores = {'Data': lista_data, 'Valor': lista_valor}

# criando um dataframe passando o dicionario como argumento
df_petroleo = pd.DataFrame(dic_valores)

# precisamos converter a coluna Valor para numeric e a coluna Data para date
# substituir virgula por ponto para poder converter o valor em decimal
df_petroleo.Valor = df_petroleo.Valor.str.replace(',', '.')

# converter a coluna Valor para Numeric
df_petroleo.Valor = pd.to_numeric(df_petroleo.Valor)

# converter a coluna Data para o tipo Data
df_petroleo.Data = pd.to_datetime(df_petroleo.Data, format="%d/%m/%Y")

# ordenando o dataframe em ordem crescente de data
df_petroleo = df_petroleo.sort_values(by=['Data'])

df_petroleo['Ano'] = df_petroleo['Data'].dt.year

# obtendo o valor medio
# df_petroleo['Ano'] = df_petroleo.Data.dt.year
valor_medio = df_petroleo.groupby('Ano')['Valor'].mean()
df_valor_medio = pd.DataFrame(valor_medio)
df_valor_medio['diff'] = df_valor_medio['Valor'].diff()
df_valor_medio = df_valor_medio.sort_values('Ano', ascending=True)



# criar um select box para armazenar os anos
anos = df_petroleo['Ano'].unique()
ano_selecao_inicio = st.sidebar.selectbox('Ano Inicio', anos)
ano_selecao_fim = st.sidebar.selectbox('Ano Fim', anos)

df_petroleo = df_petroleo.query('Ano >= @ano_selecao_inicio and Ano <= @ano_selecao_fim')

st.sidebar.title('Download Dados Filtrados')

st.sidebar.markdown('Nome do Arquivo')
coluna1, coluna2 = st.columns(2)
with coluna1:
   nome_arquivo = st.sidebar.text_input('', label_visibility='collapsed', value='dados')
   nome_arquivo += '.csv'
with coluna2:
   st.sidebar.download_button('Fazer o download da tabela em csv', data = converte_csv(df_petroleo), file_name=nome_arquivo, mime='text/csv', on_click=mensagem_sucesso)   
############################################################


st.header(f'Valor Médio do Barril nos últimos anos')
qtd_anos = st.number_input('Qtde de Anos para gerar o gráfico: Filtro exclusivo', 2, 10,4)

## CONSTRUINDO GRAFICOS
df_valor_medio.query('Ano >= @ano_selecao_inicio and Ano <= @ano_selecao_fim')
fig_media_amual = px.bar(df_valor_medio.sort_values('Ano', ascending=False)[:qtd_anos], 
                          x = df_valor_medio.sort_values('Ano', ascending=False)[:qtd_anos].index, 
                          y = 'Valor', 
                          text_auto=True)



fig_media_amual.update_layout(yaxis_title= 'Media Anual')
fig_media_amual.update_layout(xaxis_title= 'Ano')


st.plotly_chart(fig_media_amual, use_container_width=True)

st.header(f'Variação do preço médio nos últimos {qtd_anos} anos')
st.text(f'Avaliação da direita para a esquerda')

with st.container(border=True):
    
    anos = df_valor_medio.sort_values('Ano', ascending=False)[:qtd_anos].index
    cols = st.columns(anos.size)
    for i, x in enumerate(cols):
        with cols[i]:
            texto_variacao = f'Cotação média do ano {anos[i]}'
            st.metric(f'Ano: {anos[i]}', formata_numero(df_valor_medio.loc[anos[i]]['Valor']), delta=formata_numero(df_valor_medio.loc[anos[i]]['diff']), help=texto_variacao)    



st.header('Análise da Evolução da Curva de Crescimento do valor do Barril')

curva_crescimento = px.line(x = 'Data', 
                            y='Valor', 
                            data_frame=df_petroleo,
                            title="Curva de Crescimento da Evolução do Preço do Barril")
st.plotly_chart(curva_crescimento, use_container_width=True)

st.header('Análise da Evolução da Taxa de Crescimento do valor do Barril')

#######################################################################

df_petroleo['taxa_de_crescimento'] = df_petroleo.Valor.diff()
dados_atuais = df_petroleo # df_petroleo[(df_petroleo.Data.dt.year == 2023) | (df_petroleo.Data.dt.year == 2024)]
taxa_crescimento = px.bar(x = 'Data', 
                            y='taxa_de_crescimento', 
                            data_frame=dados_atuais,
                            title="Taxa de Crescimento usando a diferenciação")
st.plotly_chart(taxa_crescimento, use_container_width=True)

#################################################################################
qtd_dias_titulo = 7
st.header(f'Media Móvel dos Dados')
qtd_dias = st.number_input('Média Móvel com Qtde de Dias:', 2, 30,7)
qtd_dias_titulo = qtd_dias
dados_atuais['media_movel_valor'] = dados_atuais['Valor'].rolling(window=qtd_dias, center=False).mean()


fig1 = (go.Scatter(x=dados_atuais['Data'], y=dados_atuais['Valor'], line={'color':'yellow'}, name='Media Diária'))
fig2 = (go.Scatter(x=dados_atuais['Data'], y=dados_atuais['media_movel_valor'], name=f'Media com Janela de {qtd_dias} dias'))

data = [fig1, fig2]


st.plotly_chart(data, use_container_width=True)

####################################################################################

# auto_correlacao = autocorrelation_plot(dados_atuais.Valor)

# auto_correlacao =  autocorrelation_plot(dados_atuais.Valor)
# st.pyplot(auto_correlacao)
# st.line_chart(auto_correlacao)

# def autocorrelation_plot1(data):
#     """Calculates and plots the autocorrelation of a time series."""
#     fig, ax = plt.subplots()
#     plt.acorr(data, maxlags=len(data))
#     plt.xlabel("Lag")
#     plt.ylabel("Autocorrelation")
#     plt.title("Autocorrelation Plot")
#     plt.xlim(-len(data), len(data))
#     plt.tight_layout()
#     return fig

# fig = autocorrelation_plot1(dados_atuais.Valor)
# st.pyplot(fig)
