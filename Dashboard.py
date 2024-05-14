import streamlit as st
import requests 
import pandas as pd
import plotly.express as px
from urllib.request import urlopen, urlretrieve, Request
from urllib.error import URLError, HTTPError
from bs4 import BeautifulSoup

import seaborn as sns
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np

st.set_page_config(layout='wide')

# funcoes
def formata_numero(valor):
    return f'{valor:.2f}'    
   

st.title('Estudo sobre a produção de petróleo no Brasil')

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


# analisando o valor medio por ano
df_petroleo['Ano'] = df_petroleo.Data.dt.year
valor_medio = df_petroleo.groupby('Ano')['Valor'].mean()

df_valor_medio = pd.DataFrame(valor_medio)
df_valor_medio['diff'] = df_valor_medio['Valor'].diff()
df_valor_medio = df_valor_medio.sort_values('Ano', ascending=True)

# analisando crise do petroleo
anos_crise = [1988, 1990, 1991, 1992, 2021] #, 1972, 1973, 1974, 1975, 1976, 1977, 1978, 1979, 1980, 1981, 1982, 1983, 1984, 1985, 1986, 1987, 1988, 1989, 1990, 1991, 1992]
df_crise = df_petroleo.query('Ano in @anos_crise').groupby('Ano')['Valor'].mean()
# st.dataframe(df_crise.head(20))


## CONSTRUINDO GRAFICOS




## VISUALIZACAO NO STREAMLIT

st.header('História do Petróleo no Brasil')
st.write('''
        "O petróleo foi descoberto no Brasil ainda no século XIX, mas a sua exploração em maior escala começou somente no período seguinte. 
        Com a extração realizada em 10 unidades da federação, em dezenas de campos petrolíferos, o país se tornou um dos maiores produtores 
        dessa matéria-prima. A descoberta do pré-sal, no ano de 2007, foi fundamental para o ganho produtivo do país. A bacia de Santos é 
        atualmente a maior produtora de petróleo do Brasil, seguida pela bacia de Campos. O principal estado produtor é o Rio de Janeiro." ''')



st.header('Crises do Petróleo')

aba1, aba2, aba3 = st.tabs(['Primeira Crise (1970/1973)', 'Segunda Crise do Petróleo (1979)', 'Terceira Crise (1991)'])
with aba1:
    st.write('''
            Teve início durante a década de 1970. Nessa época a galera descobriu que o petróleo não era uma fonte renovável e, 
            justamente pelo descobrimento da finitude do que eles chamavam “ouro negro”.
            Este novo fator fez com que os preços dos barris de petróleo triplicassem! Junto com isto, no final da década de 1960 e 
            toda década de 1970, os países membros da OPEP (Organização dos Países Exportadores de Petróleo) estavam envolvidos em grandes 
            conflitos bélicos, mas ao mesmo tempo se aliavam para combinar preços do petróleo, supervalorizando-o. 
            Este cenário completamente caótico deixou a economia dos principais consumidores de petróleo do mundo (EUA e Europa) 
            com graves problemas no arranjo de suas economias.''', )

with aba2:
    st.write('''
            Lá no finalzinho dessa década, surge um novo fator na geopolítica mundial. O Irã, um dos grandes produtores de petróleo, 
            passa a vivenciar sua Revolução Islâmica Fundamentalista. A Revolução Iraniana transformou a organização interna do país 
            e, consequentemente, isto afetou a produção de petróleo. Aliado a este fator, o Irã revolucionário entrou em guerra com o 
            Iraque, outro grande produtor. A propósito, na época, os dois países eram os maiores produtores de petróleo do mundo.

            A guerra entre Irã e Iraque afetou a produtividade de petróleo e ambos reduziram suas produções. Isso diminuiu a oferta do 
            combustível no mundo, aumentando, então, o preço do barril.''', )

with aba3:
    st.write('''
            A terceira grande crise, que merece ser destacada, rolou no início dos anos 1990. Em 1991, o Iraque, mais uma vez, entra em 
            conflito, desta vez com o Kuwait. O governo iraquiano tinha a esperança de anexar o Kuwait a seu território. Até aquele momento, 
            o Iraque contava com apoio dos EUA (reflexo da Rev. Iraniana), mas, a partir deste momento, os norte-americanos decidiram intervir 
            na situação e expulsar os iraquianos. Com isto, o Golfo Pérsico foi fechado; Iraque e Kuwait pararam de produzir petróleo naquele momento; 
            os iraquianos, antes de saírem do Kuwait incendiaram vários poços de petróleo.
            Estes fatores contribuíram para que muitas especulaçoes sobre a real situação dos países surgissem e, é claro, o preço dos barris de petróleo
            subiram gradativamente.''', )


st.header('Produção de Petróleo no Brasil')
st.write('''
        "Com a descoberta da camada do pré-sal 
         e o início de sua exploração, o Brasil se tornou um país autossuficiente em petróleo. Isso significa que a produção nacional é suficiente para suprir 
         a demanda doméstica por esse recurso. O país se estabeleceu nos últimos anos como um dos 10 maiores produtores mundiais de petróleo, ocupando hoje a 
         sétima colocação, conforme apontam os dados da Administração de Informação de Energia dos Estados Unidos (EIA, sigla em inglês). 
         A fatia nacional representava, no ano de 2020, 4% de toda a produção petrolífera no mundo.

         O Brasil é responsável por uma produção de quase três bilhões de barris de petróleo todos os dias, 2,94 bilhões para sermos mais precisos. Lembrando 
         que o barril de petróleo é a unidade utilizada internacionalmente para medir o volume de petróleo em seu estado bruto, equivalendo atualmente a 159 litros 
         em média.

        A maior parte da produção brasileira é derivada dos campos marítimos, com destaque para aqueles localizados na bacia de Campos, na porção pertencente ao 
        estado do Rio de Janeiro, que figura hoje como principal produtor nacional de petróleo. O pré-sal responde por mais de 70% da produção petrolífera no Brasil."
        ''')

st.header('Reservas de Petróleo no Brasil')
st.write('''
        ""O Brasil integra a lista dos 20 países com as maiores reservas provadas de petróleo do mundo. As reservas provadas se distinguem das reservas prováveis e 
         possíveis por terem passado por um minucioso estudo que resultou em dados de engenharia e geológicos que atestaram que essas jazidas poderiam ser utilizadas 
         para exploração comercial. No ano de 2020, as reservas nacionais ocupavam a 15ª colocação e representavam 1% das reservas mundiais de petróleo, comumente 
         alternando a sua posição no ranking com o Qatar, país do Oriente Médio.

        De acordo com os dados da Agência Nacional do Petróleo, Gás Natural e Biocombustíveis (ANP), o Brasil possuía, em 2020, um total de 11,89 bilhões de barris de 
         petróleo em reservas provadas. Levando em consideração as reservas provadas, prováveis e possíveis, esse valor quase dobrou e atingiu 20,273 bilhões de reservas 
         petrolíferas no subsolo brasileiro. O Instituto Brasileiro do Petróleo e Gás (IBP) indica ainda que a grande maioria das reservas brasileiras, aproximadamente 95% 
         delas, concentra-se nas bacias de Campos e de Santos, que compreendem o litoral sudeste no país."
        ''')


# st.header(f'Valor Médio do Barril nos últimos anos')
# qtd_anos = st.number_input('Qtde de Anos', 2, 10,4)

# ## CONSTRUINDO GRAFICOS
# fig_media_amual = px.bar(df_valor_medio.sort_values('Ano', ascending=False)[:qtd_anos], 
#                           x = df_valor_medio.sort_values('Ano', ascending=False)[:qtd_anos].index, 
#                           y = 'Valor', 
#                           text_auto=True)
# fig_media_amual.update_layout(yaxis_title= 'Media Anual')
# fig_media_amual.update_layout(xaxis_title= 'Ano')


# st.plotly_chart(fig_media_amual, use_container_width=True)

# st.header(f'Variação do preço médio nos últimos {qtd_anos} anos')
# st.text(f'Avaliação da direita para a esquerda')

# with st.container(border=True):
    
#     anos = df_valor_medio.sort_values('Ano', ascending=False)[:qtd_anos].index
#     cols = st.columns(anos.size)
#     for i, x in enumerate(cols):
#         with cols[i]:
#             texto_variacao = f'Cotação média do ano {anos[i]}'
#             st.metric(f'Ano: {anos[i]}', formata_numero(df_valor_medio.loc[anos[i]]['Valor']), delta=formata_numero(df_valor_medio.loc[anos[i]]['diff']), help=texto_variacao)    

  


    