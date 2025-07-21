
##Assistente Virtual
##lembre de acessar o site Groq e criar o .env


import streamlit as st
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
import psycopg2
import os

# Inicializar o estado de visibilidade do botão de salvar e os resultados
if 'mostrar_salvar' not in st.session_state:
    st.session_state['mostrar_salvar'] = False
if 'resultados' not in st.session_state:
    st.session_state['resultados'] = None

# Função para carregar os dados existentes do CSV
def carregar_dados_csv(nome_arquivo="historico_consultas.csv"):
    try:
        return pd.read_csv(nome_arquivo)
    except FileNotFoundError:
        return pd.DataFrame(columns=['Pergunta', 'Resultados'])

# Função para salvar os dados no CSV
def salvar_dados_csv(df, nome_arquivo="historico_consultas.csv"):
    df.to_csv(nome_arquivo, index=False)


# estabelecendo conexão com banco de dados
try:
    connection = psycopg2.connect(host='localhost', database='db_crimes', user='postgres', password='1234')
    cursor = connection.cursor()
except psycopg2.Error as e:
    st.error(f"Erro ao conectar ao banco de dados: {e}")
    st.stop()


#acessando as credenciais do Groq
load_dotenv()
api_key = os.getenv("groq_api_key")


#conectar ao Groq pela api_key
client = Groq(api_key=api_key)

#configurar o layout do streamlit

st.set_page_config(page_title="Assistente de IA",layout="wide")
st.title("Assistente de Insights de Dados")


st.subheader("Banco de Dados db_crime:")
pergunta = st.text_input('Digite sua pergunta:', key='pergunta_db')

if st.button('Perguntar'):
    prompt = f"""
    Você é um assistente capaz de gerar comandos SQL para um banco de dados PostgreSQL.
    Aqui está o schema do banco de dados:

    Tabela: public.cvli (nunca esqueça o FROM)
    Colunas:
    - id (SERIAL, PRIMARY KEY)
    - municipio (TEXT) (Fortaleza,Pentecoste,Itarema,Crateus,Sobra,Caucaia) (todos no formado letra maiúscula e minúscula)
    - ais (TEXT)
    - natureza (TEXT) (HOMICIDIO DOLOSO,ROUBO SEGUIDO DE MORTE (LATROCINIO),FEMINICIDIO,LESAO CORPORAL SEGUIDA DE MORTE)
    - data_ocorrido (TEXT)
    - dia_semana (TEXT) (Segunda,Terca,Quarta,Quinta,Sexta,Sabado,Domingo)
    - meio_empregado (TEXT)
    - genero (TEXT) (Masculino,Feminino)
    - idade (TEXT)
    - escolaridade (TEXT)
    - raca_vitima (TEXT) (Indigena,Nao informada,Parda,Branca)


    Com base nesse schema, gere um comando SQL para responder à seguinte pergunta: "{pergunta}"

    Retorne somente o comando SQL, sem texto, explicações adicionais ou qualquer outra forma de comunicação.
    Obrigado.
    """
    resposta = client.chat.completions.create(
        model='llama3-70b-8192',
        messages=[
            {
                "role":"user",
                "content": prompt
            },
        ],
    )

    st.write(resposta.choices[0].message.content)
    resposta_llm = resposta.choices[0].message.content
    # Remover formatação Markdown (```) se presente
    if resposta_llm.startswith("```") and resposta_llm.endswith("```"):
        resposta_llm = resposta_llm[3:-3].strip()

    st.write("Comando SQL Gerado:")
    st.code(resposta_llm, language='sql')  # Exibe o comando SQL formatado

    try:
        cursor.execute(resposta_llm)
        connection.commit()  # Se for um comando de escrita (INSERT, UPDATE, DELETE)
        st.session_state['resultados'] = cursor.fetchall() # Salva os resultados no session state
        st.subheader("Resultados da Consulta:")
        st.dataframe(st.session_state['resultados']) # Exibe os resultados do session state
        #print(st.session_state['resultados'])  # Imprime os resultados no console
        st.session_state['mostrar_salvar'] = True # Ativa a visibilidade do botão de salvar
    except psycopg2.Error as e:
        st.error(f"Erro ao executar o comando SQL: {e}")
        st.session_state['mostrar_salvar'] = False # Garante que o botão de salvar não apareça em caso de erro
        st.session_state['resultados'] = None
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
        st.session_state['mostrar_salvar'] = False # Garante que o botão de salvar não apareça em caso de erro
        st.session_state['resultados'] = None

if st.session_state['mostrar_salvar']:
    if st.button('Salvar no CSV'):
        # Salvar a pergunta e os resultados no CSV
        historico_df = carregar_dados_csv()
        novo_registro = pd.DataFrame([{'Pergunta': pergunta, 'Resultados': str(st.session_state['resultados'])}]) # Usa os resultados do session state
        historico_df = pd.concat([historico_df, novo_registro], ignore_index=True)
        salvar_dados_csv(historico_df)
        st.success("A pergunta e os resultados foram salvos em 'historico_consultas.csv'")
        st.session_state['mostrar_salvar'] = False # Desativa o botão após salvar (opcional)

if connection:
    cursor.close()
    connection.close()
    print('Conexão Fechada')

st.subheader("Tire Insights de um CSV para criação de Dashboards no PowerBi:")

upload_file = st.file_uploader('Faça o upload do arquivo csv', type=['csv'])

if upload_file:
    df = pd.read_csv(upload_file,sep=';')
    st.subheader("Prévia do arquivo csv")
    st.dataframe(df.head())
    resposta_user = st.text_input('Digite sua pergunta:',key='pergunta_csv')


if st.button('Enviar'):
    colunas = ", ".join(df.columns)
    linhas =df.head().to_csv(index=False)
    prompt = f"""
Você é um assistente de análise de dados. Um usuário enviou um arquivo CSV com as seguintes colunas: {colunas}.
Aqui estão algumas linhas do dataset:

{linhas}

Com base nesses dados responda:
{resposta_user}
"""

    resposta = client.chat.completions.create(
        model='llama3-70b-8192',
        messages=[
            {
                "role":"user",
                "content": prompt
            },
        ],
    )
    #print('I.A: '+resposta.choices[0].message.content)
    st.write(resposta.choices[0].message.content,key='resp_Enviar')

if st.button('Gerar insights'):
    colunas = ", ".join(df.columns)
    linhas =df.head().to_csv(index=False)

    prompt = f"""
Você é um assistente de análise de dados. Um usuário enviou um arquivo CSV com as seguintes colunas: {colunas}.
Aqui estão algumas linhas do dataset:

{linhas}

Com base nesses dados:
1. Sugira possíveis análises estatísticas ou de negócio que podem ser feitas.
2. Sugira tipos de gráficos adequados.
3. Aponte insights ou padrões visíveis mesmo com poucos dados.
4. Sugira análise de hipóteses ou perguntas que podem ser feitas com esses dados.
5. Não explique o que é um CSV ou termos básicos — foque na análise.

Retorne os resultados de forma estruturada e em Português do Brasil.
"""
    with st.spinner("Gerando insights..."):
        resposta = client.chat.completions.create(
            model ='llama3-70b-8192',
            messages=[
                {
                    "role":"user",
                    "content": prompt
                },
            ],
        )
        resposta_llm = resposta.choices[0].message.content

    st.subheader("Insights Gerado: ")
    st.markdown(resposta_llm)
