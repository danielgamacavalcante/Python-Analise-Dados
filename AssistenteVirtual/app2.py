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
if 'resultados_df' not in st.session_state:
    st.session_state['resultados_df'] = pd.DataFrame()
if 'resultados2' not in st.session_state:
    st.session_state['resultados2'] = None
if 'resultados2_df' not in st.session_state:
    st.session_state['resultados2_df'] = pd.DataFrame()
if 'resposta_llm' not in st.session_state:
    st.session_state['resposta_llm'] = None

# Função para carregar os dados existentes do CSV (histórico de consultas)
def carregar_dados_csv(nome_arquivo="historico_consultas.csv"):
    try:
        return pd.read_csv(nome_arquivo)
    except FileNotFoundError:
        return pd.DataFrame(columns=['Pergunta', 'Resultados'])

# Função para salvar os dados no CSV (histórico de consultas)
def salvar_dados_csv(df, nome_arquivo="historico_consultas.csv"):
    df.to_csv(nome_arquivo, index=False)

# Função para salvar a pergunta e os resultados agrupados no CSV dedicado
def salvar_agrupamentos_csv(pergunta, resultados_df, nome_arquivo="agrupamentos.csv"):
    df_agrupado = pd.DataFrame([{'Pergunta': pergunta, 'Resultados': resultados_df.to_json()}])
    try:
        existente_df = pd.read_csv(nome_arquivo)
        df_final = pd.concat([existente_df, df_agrupado], ignore_index=True)
    except FileNotFoundError:
        df_final = df_agrupado
    df_final.to_csv(nome_arquivo, index=False)

# Função para carregar a pergunta e os resultados agrupados do CSV dedicado
def carregar_agrupamentos_csv(nome_arquivo="agrupamentos.csv"):
    try:
        return pd.read_csv(nome_arquivo)
    except FileNotFoundError:
        return pd.DataFrame(columns=['Pergunta', 'Resultados'])

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

#Puxando o cabeçalho
try:
    st.subheader("Header de Dados db_crime:")
    cursor.execute('Select * from public.cvli limit 5')
    resultados_header = cursor.fetchall()
    # Obtenha os nomes das colunas do cursor
    nomes_colunas = [desc[0] for desc in cursor.description]
    # Combine os nomes das colunas com os resultados em um DataFrame
    st.session_state['header_df'] = pd.DataFrame(resultados_header, columns=nomes_colunas)
    st.dataframe(st.session_state['header_df']) # Exibe o DataFrame do cabeçalho
except Exception as e:
    st.error(f"Ocorreu um erro inesperado ao exibir o cabeçalho: {e}")


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
    - data_ocorrido (TEXT) (formato PT-br)
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

    st.session_state['resposta_llm'] = resposta.choices[0].message.content
    resposta_llm = st.session_state['resposta_llm']
    # Remover formatação Markdown (```) se presente
    if resposta_llm.startswith("```") and resposta_llm.endswith("```"):
        resposta_llm = resposta_llm[3:-3].strip()

    st.write("Comando SQL Gerado:")
    st.code(resposta_llm, language='sql')  # Exibe o comando SQL formatado

    try:
        cursor.execute(resposta_llm)
        # connection.commit()  # Se for um comando de escrita (INSERT, UPDATE, DELETE)
        resultados = cursor.fetchall() # Obtém os resultados
        nomes_colunas_resultados = [desc[0] for desc in cursor.description]
        st.session_state['resultados_df'] = pd.DataFrame(resultados, columns=nomes_colunas_resultados) # Salva como DataFrame
        # st.subheader("Resultados da Consulta:")
        # st.dataframe(st.session_state['resultados_df']) # Exibe o DataFrame
        st.session_state['mostrar_salvar'] = True # Ativa a visibilidade do botão de salvar
    except psycopg2.Error as e:
        st.error(f"Erro ao executar o comando SQL: {e}")
        st.session_state['mostrar_salvar'] = False # Garante que o botão de salvar não apareça em caso de erro
        st.session_state['resultados_df'] = pd.DataFrame()
    except Exception as e:
        st.error(f"Ocorreu um erro inesperado: {e}")
        st.session_state['mostrar_salvar'] = False # Garante que o botão de salvar não apareça em caso de erro
        st.session_state['resultados_df'] = pd.DataFrame()

# Exibe o DataFrame de resultados (se existir) fora do botão 'Perguntar'
if not st.session_state['resultados_df'].empty:
    st.subheader("Resultados da Consulta:")
    st.dataframe(st.session_state['resultados_df'])

if st.session_state['mostrar_salvar']:
    if st.button('Salvar no CSV'):
        # Salvar a pergunta e os resultados NO HISTÓRICO
        historico_df = carregar_dados_csv()
        novo_registro = pd.DataFrame([{'Pergunta': pergunta, 'Resultados': st.session_state['resultados_df'].to_json()}]) # Salva DataFrame como JSON
        historico_df = pd.concat([historico_df, novo_registro], ignore_index=True)
        salvar_dados_csv(historico_df)
        st.success("A pergunta e os resultados foram salvos em 'historico_consultas.csv'")
        st.session_state['mostrar_salvar'] = False # Desativa o botão após salvar (opcional)

if st.button('Agrupar'):
    if st.session_state['resposta_llm']:
        resposta_llm = st.session_state['resposta_llm']
        if resposta_llm.startswith("```") and resposta_llm.endswith("```"):
            resposta_llm = resposta_llm[3:-3].strip()
        st.code(resposta_llm, language='sql')
        try:
            cursor.execute(resposta_llm)
            resultados2 = cursor.fetchall() # Obtém os resultados agrupados
            nomes_colunas_agrupados = [desc[0] for desc in cursor.description]
            st.session_state['resultados2_df'] = pd.DataFrame(resultados2, columns=nomes_colunas_agrupados) # Salva como DataFrame

            # Salvar a pergunta e os resultados agrupados no CSV dedicado
            salvar_agrupamentos_csv(pergunta, st.session_state['resultados2_df'])
            st.info("A pergunta e os resultados agrupados foram salvos em 'agrupamentos.csv'")
            
        except psycopg2.Error as e:
            st.error(f"Erro ao executar o comando SQL de agrupamento: {e}")
        except Exception as e:
            st.error(f"Ocorreu um erro inesperado ao agrupar os dados: {e}")
    else:
        st.warning("Por favor, execute uma pergunta primeiro para gerar um comando SQL.")

# Carregar e exibir o conteúdo do CSV de agrupamentos
df_agrupamentos = carregar_agrupamentos_csv()
if not df_agrupamentos.empty:
    st.subheader("Histórico de Agrupamentos:")
    st.dataframe(df_agrupamentos)

    pergunta = st.text_input('Digite sua pergunta:', key='pergunta_csv_agrupado')

    if st.button('Pergunte'):
        df = pd.read_csv('agrupamentos.csv',sep=';')
        colunas = ", ".join(df.columns)
        linhas = df.to_csv(index=False)

        prompt = f"""
        Você é um assistente de análise de dados. Com base em um CSV com as seguintes colunas: {colunas}.
        Aqui estão algumas linhas do dataset:

        {linhas}

        Com base nesses dados responda:
        {pergunta}

        Retorne os resultados de forma direta e claro, sem arrodeios e em Português do Brasil.
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

        st.write(resposta.choices[0].message.content,key='resp_pergunte')

else:
    st.info("Nenhum agrupamento salvo ainda.")

if connection:
    cursor.close()
    connection.close()
    print('Conexão Fechada')