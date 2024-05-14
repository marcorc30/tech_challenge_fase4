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
from prophet import Prophet




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


st.title('Previsões - Séries Temporais (Prophet)')

st.write(''' 
        Prophet é um procedimento para previsão de dados de séries temporais com base em 
         um modelo aditivo onde tendências não lineares são ajustadas à sazonalidade anual, 
         semanal e diária, além dos efeitos dos feriados. Funciona melhor com séries temporais 
         que apresentam fortes efeitos sazonais e várias temporadas de dados históricos. 
         O Prophet é robusto em relação à falta de dados e às mudanças na tendência e normalmente
        lida bem com valores discrepantes.

         Foram criados 5 modelos, onde o refinamento foi feito alterando os hiperparâmetros para se chegar
         a um modelo com a menor variação de erro possível.  
        ''')


# st.sidebar.title('Filtros')



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

dados_atuais = df_petroleo[(df_petroleo.Data.dt.year == 2023) | (df_petroleo.Data.dt.year == 2024)]


# A entrada para o Prophet é sempre um dataframe com duas colunas: ds e y.
# A coluna ds (datestamp) deve ter um formato esperado pelo Pandas, idealmente AAAA-MM-DD para uma data ou AAAA-MM-DD HH:MM:SS
# para um carimbo de data/hora. A coluna y deve ser numérica e representa a medida que desejamos prever, no nosso caso, o valor do barril;



mod1, mod2, mod3, mod4, mod5, metricas = st.tabs(['Modelo1', 'Modelo2', 'Modelo3', 'Modelo4', 'Modelo5', 'Métricas'])

with mod1:
    df = pd.DataFrame()
    df['ds'] = dados_atuais.Data
    df['y'] = dados_atuais.Valor

    # criando o modelo (v1)
    modelo = Prophet()

    # treinando o modelo
    modelo.fit(df)

    # informando o numero de dias que sera feita a previsao (em dias)
    dataframefuturo = modelo.make_future_dataframe(periods=30)

    previsao = modelo.predict(dataframefuturo)

    grafico = modelo.plot(previsao, xlabel='Data', ylabel='Valor');

    # st.plotly_chart(grafico, use_container_width=True)
    st.write('''No primeiro modelo, foi usado a configuração padrão do prophet. Podemos observar
             que o modelo não está ajustado, pois os valores estão muito fora do intervalo de 
             confiança. ''')
    st.write(grafico)

with mod2:
    st.write('''
    Nesse segundo modelo, vamos dividir os dados entre treino e teste.

    Nesse gráfico, podemos observar o mesmo gráfico anterior, com a diferença que agora temos os pontos em
    vermelho, que são os dados de teste. Podemos observar que nosso modelo não está prevendo de forma correta,
    pois os pontos vermelhos estão muito fora do intervalo de confiança, e muito afastados da previsão (linha azul) ''')
    # dados treino
    df = pd.DataFrame()
    df['ds'] = dados_atuais.Data[:300] # filtrando os dados até a posicao 300
    df['y'] = dados_atuais.Valor[:300] # filtrando os dados até a posicao 300

    # dados teste
    df_teste = pd.DataFrame()
    df_teste['ds'] = dados_atuais.Data[300:] # filtrando os dados de 300 pra frente
    df_teste['y'] = dados_atuais.Valor[300:] # filtrando os dados de 300 pra frente    

    modelo = Prophet()
    modelo.fit(df)
    dataframefuturo = modelo.make_future_dataframe(periods=29)
    previsao = modelo.predict(dataframefuturo)
    grafico1 = modelo.plot(previsao, xlabel='Data', ylabel='Valor');
    # plotando os 29 de teste e comparando com a previsão
    plt.plot(df_teste.ds, df_teste.y, '.r')
    componentes = modelo.plot_components(previsao, figsize=(10,6));

    st.write(grafico1, use_container_width=True)
    st.plotly_chart(componentes, use_container_width=True)    
   
with mod3:

    st.write('''
    Por padrão, o prophet faz a análise de tendência (padrão de crescimento/decrescimento) do gráfico de forma linear. Esse comportamento é muito importante para fazer as previsões, pois elas serão realizadas de acordo com um padrão do passado.
    Será que essa tendência do gráfico anterior está correta? Não poderíamos alterar alguns parâmetros para ajustar a tendência nos pontos? Podemos ajustar esse pontos de tendência um pouco mais para ajudar nosso modelo?
    Vamos agora ajustar os pontos de tendência para melhor ajustar o modelo. Para isso, vamos usar a add_changepoints_to_plot.
    Pontos de tendência são pontos onde existe uma mudança de rumo na linha de tendência.
             
    Essa mudança de tendência é muito importante para o modelo. Pois ela é o comportamento que os dados tem
    em um determinado período, e não segnifica que no período completo a tendẽncia tenha o mesmo comportamento.
    No gráfico abaixo, estamos ajustando vários segmentos de reta para períodos de tempo na série temporal.
    Nesse primeiro momento, vamos deixar o prophet localizar esses pontos de mudanças de tendência             
    ''')
    from prophet.plot import add_changepoints_to_plot

    # Visualizando os change points => pontos de mudança de tendência

    # Essa mudança de tendência é muito importante para o modelo. Pois ela é o comportamento que os dados tem
    # em um determinado período, e não segnifica que no período completo a tendẽncia tenha o mesmo comportamento.
    # No gráfico abaixo, estamos ajustando vários segmentos de reta para períodos de tempo na série temporal.
    # Nesse primeiro momento, vamos deixar o prophet localizar esses pontos de mudanças de tendência

    # Plotando o modelo
    fig = modelo.plot(previsao)
    # Adicionando os pontos de mudança de tendência (linha vermelha vertical)
    a = add_changepoints_to_plot(fig.gca(), modelo, previsao)

    st.write(fig, use_container_width=True)

    # Por padrão, o prophet configura o crescimento do gráfico com uma tendência linear. Mas como podemos observar no
    # gráfico, ele apresenta um formato de "s" (siguimoide), que indica uma tendência logística, que envolve um
    # crescimento exponencial, seguido de uma redução constante, até uma estabilização, assumindo uma curva em
    # formato de "S"

    # Podemos forçar o prophet a identificar um número maior de changepoints no decorrer da linha do gráfico. Isso
    # ajudará o modelo nas previsões para identificar futuras mudança de tendências para os dados previstos.

    # n_changepoints => altera o número de changepoints (quantidade de recortes na tendencia)
    # changepoint_prior_scale => aumenta a área na série temporal onde ele pode enxergar changepoints. Padrao 0.05.
    # changepoint_prior_scale é como se estivéssemos colocando uma lupa sobre o gráfico e identificando tendências
    # mais sutis.

    # Caso tenhamos datas que temos certeza de alteração de tendência, podemos inclui-la manualmente
    # changepoints= ['01.01.2023'] => podemos adicionar changepoints específicos

    # linha vermelha horizontal => tendencia da serie temporal
    # linha vermelha vertical => changepoints
    # Obs: Temos que alterar esses parâmetros com caulela, pois podemos criar um overfitting (ajustar demais os dados
    # ao modelo, e dificultar a generalização)


    modelo = Prophet(n_changepoints=25, changepoint_prior_scale=0.05)

    # podemos também adicionar changepoints especificos
    # modelo = Prophet(changepoints=['2023-10-03'])

    modelo.fit(df)
    dataframefuturo = modelo.make_future_dataframe(periods=29)
    previsao = modelo.predict(dataframefuturo)
    fig2 = modelo.plot(previsao, xlabel='Data', ylabel='Valor');
    # plotando os 29 dias restantes
    plt.plot(df_teste.ds, df_teste.y, '.r')

    a = add_changepoints_to_plot(fig.gca(), modelo, previsao)    
    st.write(fig2, use_container_width=True)

with mod4:
    st.write('''
    Novo modelo ajustando os feriados, sazonalidade e finais de semana

    Como não temos cotação aos finais de semana, temos que informar ao modelo quais são os dias 
    que ele não deverá "processar" para fazer a previsão. Vamos informar também os feriados nacionais,
    para ver se há alguma interferência na previsão.
''')
    # Adicionando no modelo os feriados do Brasil
    # Obs: caso tivéssemos paralização também nos feriados regionais, poderíamos criar um df com nome feriados
    # e incluir no modelo da seguinte forma:
    # modelo = Prophet(n_changepoints=25, changepoint_prior_scale=10, hollidays=feriados)


    modelo = Prophet(n_changepoints=25)
    modelo.add_country_holidays(country_name='BR')

    modelo.fit(df)
    dataframefuturo = modelo.make_future_dataframe(periods=51)
    previsao = modelo.predict(dataframefuturo)
    fig3 = modelo.plot(previsao, xlabel='Data', ylabel='Valor');
    # plotando os 29 dias restantes
    plt.plot(df_teste.ds, df_teste.y, '.r')

    a = add_changepoints_to_plot(fig.gca(), modelo, previsao)

    st.write(fig3, use_container_width=True)

    # from sklearn.metrics import mean_absolute_error

    # # abaixo percebemos que ao alterar a sazonalidade para multiplicativa, a taxa de erro diminuiu consideravelmente

    # # sazonalidade aditiva
    # st.text(f'Sozonalidade Aditiva: {mean_absolute_error(df["y"], previsao["yhat"][:300])}')

    # # sazonalidade multiplicativa
    # st.text(f'Sozonalidade Aditiva: {mean_absolute_error(df["y"], previsao_multiplicativa["yhat"][:300])}')

    # # print(f'Sozonalidade Aditiva: mean_absolute_error(df["y"], previsao_multiplicativa["yhat"][:300])}')

with mod5:
    st.write('''
    Criando um novo dataframe para se retirar os outliers.
    No nosso caso, vamos definir outiliers como os dados fora do intervalo de confiança. Pode ter ocorrido
    um evento qualquer em determinados dias que fez os valor do barril subir ou descer abruptamente.
    Como é um evento esporárido, podemos excluí-los para não prejudicar nosso modelo.

    ''')
    novo_y = df.reset_index()
    df_sem_outlier = novo_y[(novo_y.y > previsao['yhat_lower'][:300]) & (novo_y.y < previsao['yhat_upper'][:300])]

    modelo = Prophet(n_changepoints=25,changepoint_prior_scale=1.0)
    modelo.add_country_holidays(country_name='BR')

    modelo.fit(df_sem_outlier)
    dataframefuturo = modelo.make_future_dataframe(periods=51)
    previsao = modelo.predict(dataframefuturo)

    fig = modelo.plot(previsao, xlabel='Data', ylabel='Valor');
    # plotando os 51 dias restantes
    plt.plot(df_teste.ds, df_teste.y, '.r')
    
    # st.write(fig, use_container_width=True)

    st.pyplot(fig, use_container_width=True)

    st.write('Dados com e sem Outiliers')  

    fig1 = (go.Scatter(x=df.index, y=df['y'],  line={'color':'yellow'}, name='Com outiliers'))
    # fig2 = (go.Scatter(x=df_sem_outlier['index'], y=df_sem_outlier.y, mode='markers', name=f'Sem outiliers'))
    fig2 = (go.Scatter(x=df_sem_outlier['index'], y=df_sem_outlier.y, line={'color':'red'}, name=f'Sem outiliers'))

    data = [fig1, fig2]


    st.plotly_chart(data, use_container_width=True)

    st.write('''Imprimindo os componentes
             
             Aqui podemos observar  a tendência, a sazonalidade anual e a sazonalidade semanal da série temporal. 
    Aqui também podemos observar os feriados.
             ''')

    fig = modelo.plot_components(previsao, figsize=(10,6));
    st.pyplot(fig)



    # plt.figure(figsize=(10,6))
    # plt.plot(df.index, df['y'], '.r')
    # plt.plot(df_sem_outlier['index'], df_sem_outlier.y)
    # plt.legend(labels=['Com Outliers', 'Sem Outliers'])

    # st.pyplot(plt.plot(df.index, df['y'], '.r'))

with metricas:
    from prophet.diagnostics import cross_validation
    from prophet.diagnostics import performance_metrics
    from prophet.plot import plot_cross_validation_metric

    st.write('''
        Validação Cruzada.
        O Prophet inclui funcionalidade para validação cruzada de séries temporais para medir erros
        de previsão usando dados históricos. Isso é feito selecionando pontos de corte no histórico,
        e para cada um deles ajustando o modelo utilizando dados apenas até aquele ponto de corte.
    
        Podemos observar que dividimos em 8 períodos
        cutoff => pontos de corte
        ''')
    df_cv = cross_validation(modelo, initial='180 days', period='30 days', horizon='30 days')
    cutoff = df_cv['cutoff'].unique()

    st.write("cross_validation(modelo, initial='180 days', period='30 days', horizon='30 days')")
    st.write(f'{cutoff.size} é a quantidade de períodos')
    # st.write(f'{cutoff}')    

    janela = 1

    # fig = plt.figure(figsize=(20,10))
    # ax = fig.add_subplot(111)
    # ax.plot(modelo.history['ds'].values, modelo.history['y'], 'k.')
    # ax.plot(df_cv_cut['ds'].values, df_cv_cut['yhat'], ls='-', c='#0072B2')
    # ax.fill_between(df_cv_cut['ds'].values, df_cv_cut['yhat_lower'],
    #                 df_cv_cut['yhat_upper'], color='blue',
    #                                 alpha=0.2)
    # ax.axvline(x=pd.to_datetime(cutoff), c='gray', lw=4, alpha=0.5)
    # ax.set_ylabel('y')
    # ax.set_xlabel('ds')

    df_p = performance_metrics(df_cv)

    
    st.write('''O MAPE (Erro Médio Absoluto Percentual) é uma métrica de erro que é muito utilizada
              em séries temporais, principalmente para previsões de demanda. Assim como explicado na 
             seção de diferença entre erro absoluto e relativo, a diferença é que o MAPE é a média 
             dos erros relativos. ''')

    st.table(df_p[['horizon', 'mape']])


    plot = plot_cross_validation_metric(df_cv, metric='mape')
    plt.title('MAPE (Erro Médio Absoluto Percentual)')
    st.pyplot(plot)



   
       
