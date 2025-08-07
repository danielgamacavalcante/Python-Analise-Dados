# app.py
import gradio as gr
from gradio.components import Markdown
import google.generativeai as genai  #utilizado para IA, API Gemini
from dotenv import load_dotenv #utilizado para ler a chave do API Gemini
import re
import pandas as pd
import psycopg2
# import matplotlib.pyplot as plt
import os
from io import BytesIO
import base64
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

# DB_HOST = os.getenv("DB_HOST")
# DB_NAME = os.getenv("DB_NAME")
# DB_USER = os.getenv("DB_USER")
# DB_PASSWORD = os.getenv("DB_PASSWORD")
# DB_PORT = os.getenv("DB_PORT")

# --- 1. Configurações do Banco de Dados ---
DB_HOST = "localhost"
DB_NAME = "db_financeiro"
DB_USER = "postgres"
DB_PASSWORD = "1234"
DB_PORT = "5432"

def get_db_connection():
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            port=DB_PORT
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None

def get_anos_disponiveis():
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        query = """
        SELECT DISTINCT EXTRACT(YEAR FROM data_venda) AS ano
        FROM DW_FINANCEIRO.FATO
        ORDER BY ano DESC;
        """
        cursor.execute(query)
        anos = [str(ano[0]) for ano in cursor.fetchall()]
        return anos
    except Exception as e:
        print(f"Erro ao obter anos disponíveis: {e}")
        return []
    finally:
        if conn:
            conn.close()
            
def handle_select_all_categories(select_all, all_choices,current_categories):
    """
    Função de callback para o checkbox "Selecionar Tudo".
    Se o checkbox for True, retorna todas as categorias.
    Se for False, retorna apenas o primeiro item da lista.
    """
    if select_all:
        return all_choices
    else:
        return current_categories
#================================================ Função da IA Gemini ====================================================
SCHEMA_DO_SEU_DATA_WAREHOUSE = """
Você é um assistente de IA especializado em PostgreSQL. Sua única tarefa é traduzir perguntas em português para consultas SQL.

**Restrição de Segurança:**
- GERE APENAS CONSULTAS QUE COMECEM COM `SELECT`.
- NENHUMA OUTRA INSTRUÇÃO SQL (como INSERT, UPDATE, DELETE, DROP, ALTER, etc.) É PERMITIDA.

Use o esquema a seguir:

Tabelas:
- DW_FINANCEIRO.FATO (id, data_venda, data_entrega, id_canal, id_cliente, id_produto, qtde, valor_total)
- DW_FINANCEIRO.MARCA (id, marca)
- DW_FINANCEIRO.CATEGORIA (id, categoria)
- DW_FINANCEIRO.CANAL (id, descricao_canal)
- DW_FINANCEIRO.CLIENTES (id, nome, sobrenome, data_nascimento, estado_civil, genero, educacao, id_cidade)
- DW_FINANCEIRO.CIDADE (id, cidade, uf)
- DW_FINANCEIRO.PRODUTO (id, descricao_produto, id_subcategoria, id_marca, preco_unitario, tributos, custo)
- DW_FINANCEIRO.SUBCATEGORIA (id, subcategoria, id_categoria)

Relacionamentos:
- DW_FINANCEIRO.FATO.id_canal -> DW_FINANCEIRO.CANAL.id
- DW_FINANCEIRO.FATO.id_cliente -> DW_FINANCEIRO.CLIENTES.id
- DW_FINANCEIRO.FATO.id_produto -> DW_FINANCEIRO.PRODUTO.id
- DW_FINANCEIRO.CLIENTES.id_cidade -> DW_FINANCEIRO.CIDADE.id
- DW_FINANCEIRO.PRODUTO.id_marca -> DW_FINANCEIRO.MARCA.id
- DW_FINANCEIRO.PRODUTO.id_subcategoria -> DW_FINANCEIRO.SUBCATEGORIA.id
- DW_FINANCEIRO.SUBCATEGORIA.id_categoria -> DW_FINANCEIRO.CATEGORIA.id

As tabelas de fato e dimensão podem ser unidas usando as colunas de ID correspondentes.
"""
# Carrega as variáveis de ambiente do arquivo .env
load_dotenv()
# Obtém a chave de API do ambiente
api_key = os.getenv("GOOGLE_API_KEY")

if not api_key:
    raise ValueError("Chave de API não encontrada. Verifique o arquivo .env.")

def execute_ai_query(pergunta_usuario):
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')

    prompt_completo = f"{SCHEMA_DO_SEU_DATA_WAREHOUSE}\n\nTraduza a seguinte pergunta para uma consulta SQL:\n'{pergunta_usuario}'"
    sql_query = ""
    
    try:
        response = model.generate_content(prompt_completo)
        sql_query = response.text.strip()
        
        sql_query_limpa = re.sub(r"```sql\s*|```", "", sql_query, flags=re.IGNORECASE).strip()
        
        if sql_query_limpa.lower().startswith("select"):
            conn = get_db_connection()
            cursor = conn.cursor()
            cursor.execute(sql_query_limpa)
            dados = cursor.fetchall()
            colunas = [desc[0] for desc in cursor.description]
            df = pd.DataFrame(dados, columns=colunas)
            
            # --- CORREÇÃO ADICIONADA AQUI ---
            # Verifica as colunas se for do tipo numérico irá corrigir formatação
            for col in df.columns:
                try:
                    # Tenta converter a coluna inteira para um tipo numérico
                    df[col] = pd.to_numeric(df[col], errors='raise')
                    
                    # Verifica se a coluna agora é de tipo numérico
                    if pd.api.types.is_numeric_dtype(df[col]):
                        # Aplica a formatação de número com duas casas decimais
                        df[col] = df[col].apply(lambda x: f'{x:,.2f}' if pd.notnull(x) else None)
                except (ValueError, TypeError):
                    # Ignora a coluna se a conversão falhar (não é um número)
                    pass
          
            # -------------------------------
            
            return df.to_markdown(index=False)
        else:
            return f"Comando SQL inválido. A consulta gerada foi: `{sql_query_limpa}`. Apenas consultas SELECT são aceitas."
            
    except Exception as e:
        return f"Ocorreu um erro: {e}"
    finally:
        if 'conn' in locals() and conn:
            conn.close()
#================================================ Criação de Gráficos ====================================================            
def get_categorias_disponiveis():
    conn = get_db_connection()
    if conn is None:
        return []
    try:
        cursor = conn.cursor()
        query = """
         SELECT DISTINCT cat.categoria
        FROM DW_FINANCEIRO.FATO AS fato
        JOIN DW_FINANCEIRO.PRODUTO AS prod ON fato.id_produto = prod.id
        JOIN DW_FINANCEIRO.SUBCATEGORIA AS sub ON prod.id_subcategoria = sub.id
        JOIN DW_FINANCEIRO.CATEGORIA AS cat ON sub.id_categoria = cat.id
        ORDER BY cat.categoria;
        """
        cursor.execute(query)
        categorias = [cat[0] for cat in cursor.fetchall()]
        return categorias
    except Exception as e:
        print(f"Erro ao obter categorias disponíveis: {e}")
        return []
    finally:
        if conn:
            conn.close()
# --- 2. Funções para Gerar Gráficos (mantidas as mesmas) ---


#==== Gráfico Gerado com Matplotlib ========

# def gerar_grafico_vendas_por_mes_ano(ano_selecionado):
#     conn = get_db_connection()
#     if conn is None:
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
#     try:
#         cursor = conn.cursor()
#         query = f"""
#         SELECT
#             EXTRACT(MONTH FROM data_venda) AS mes,
#             SUM(valor_total) AS total_vendas
#         FROM
#             DW_FINANCEIRO.FATO
#         WHERE
#             EXTRACT(YEAR FROM data_venda) = {ano_selecionado}
#         GROUP BY
#             mes
#         ORDER BY
#             mes;
#         """
#         cursor.execute(query)
#         dados = cursor.fetchall()
#         df_vendas = pd.DataFrame(dados, columns=['mes', 'total_vendas'])
#         if df_vendas.empty:
#             fig, ax = plt.subplots(figsize=(12, 6))
#             ax.text(0.5, 0.5, f"Nenhum dado encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
#             ax.axis('off')
#             return fig
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.bar(df_vendas['mes'], df_vendas['total_vendas'], color='skyblue')
#         ax.set_xlabel('Mês')
#         ax.set_ylabel('Total de Vendas')
#         ax.set_title(f'Total de Vendas no ano de {ano_selecionado}')
#         plt.tight_layout()
#         return fig
#     except psycopg2.Error as e:
#         print(f"Erro ao executar a consulta SQL: {e}")
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.text(0.5, 0.5, f"Erro ao consultar dados: {e}", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
#     finally:
#         if conn:
#             conn.close()

#==== Gráfico Gerado com Plotly ========

def gerar_grafico_vendas_por_mes_ano(ano_selecionado):
    conn = get_db_connection()
    
    # Se houver erro de conexão, retorna um gráfico de erro do Plotly
    if conn is None:
        fig = go.Figure()
        fig.add_annotation(
            text="Erro ao conectar ao banco de dados.",
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title=f'Total de Vendas no ano de {ano_selecionado}',
                          xaxis_visible=False, yaxis_visible=False)
        return fig
    
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT
            EXTRACT(MONTH FROM data_venda) AS mes,
            SUM(valor_total) AS total_vendas
        FROM
            DW_FINANCEIRO.FATO
        WHERE
            EXTRACT(YEAR FROM data_venda) = {ano_selecionado}
        GROUP BY
            mes
        ORDER BY
            mes;
        """
        cursor.execute(query)
        dados = cursor.fetchall()
        df_vendas = pd.DataFrame(dados, columns=['mes', 'total_vendas'])
        
        # Se não houver dados, retorna um gráfico Plotly com uma mensagem de aviso
        if df_vendas.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Nenhum dado encontrado para o ano {ano_selecionado}.",
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title=f'Total de Vendas no ano de {ano_selecionado}',
                              xaxis_visible=False, yaxis_visible=False)
            return fig
        
        # Cria o gráfico de barras com Plotly Express
        fig = px.bar(
            df_vendas,
            x='mes',
            y='total_vendas',
            title=f'Total de Vendas no ano de {ano_selecionado}',
            labels={'mes': 'Mês', 'total_vendas': 'Total de Vendas'},
            color='mes',
            color_continuous_scale=px.colors.sequential.Teal
        )
        
        fig.update_layout(
            bargap=0.2,
            xaxis=dict(tickmode='linear', dtick=1, title='Mês'),
            yaxis=dict(title='Total de Vendas', tickformat=".2s"),
            font=dict(family="Arial", size=12),
            height=500  # Ajusta a altura do gráfico
        )
        
        return fig
        
    except psycopg2.Error as e:
        print(f"Erro ao executar a consulta SQL: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao consultar dados: {e}",
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title='Erro', xaxis_visible=False, yaxis_visible=False)
        return fig
        
    finally:
        if conn:
            conn.close()

#==== Gráfico Gerado com Matplotlib ========

# def gerar_grafico_vendas_por_canal(ano_selecionado):
#     conn = get_db_connection()
#     if conn is None:
#         fig, ax = plt.subplots(figsize=(8, 8))
#         ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
#     try:
#         cursor = conn.cursor()
#         query = f"""
#         SELECT
#             c.descricao_canal,
#             SUM(f.valor_total) AS total_vendas
#         FROM
#             DW_FINANCEIRO.FATO AS f
#         JOIN
#             DW_FINANCEIRO.CANAL AS c ON f.id_canal = c.id
#         WHERE
#             EXTRACT(YEAR FROM f.data_venda) = {ano_selecionado}
#         GROUP BY
#             c.descricao_canal
#         ORDER BY
#             total_vendas DESC;
#         """
#         cursor.execute(query)
#         dados = cursor.fetchall()
#         df_canais = pd.DataFrame(dados, columns=['descricao_canal', 'total_vendas'])
#         if df_canais.empty:
#             fig, ax = plt.subplots(figsize=(8, 8))
#             ax.text(0.5, 0.5, f"Nenhum dado de vendas por canal encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
#             ax.axis('off')
#             return fig
#         fig, ax = plt.subplots(figsize=(8, 8))
#         ax.pie(df_canais['total_vendas'], labels=df_canais['descricao_canal'], autopct='%1.1f%%', startangle=90)
#         ax.set_title(f'Vendas por Canal no ano de {ano_selecionado}')
#         plt.tight_layout()
#         return fig
#     except psycopg2.Error as e:
#         print(f"Erro ao executar a consulta SQL: {e}")
#         fig, ax = plt.subplots(figsize=(8, 8))
#         ax.text(0.5, 0.5, f"Erro ao consultar dados: {e}", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
#     finally:
#         if conn:
#             conn.close()

#==== Gráfico Gerado com Plotly ========
def gerar_grafico_vendas_por_canal(ano_selecionado):
    conn = get_db_connection()
    
    # Se houver erro de conexão, retorna um gráfico de erro do Plotly
    if conn is None:
        fig = go.Figure()
        fig.add_annotation(
            text="Erro ao conectar ao banco de dados.",
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title=f'Vendas por Canal no ano de {ano_selecionado}',
                          xaxis_visible=False, yaxis_visible=False)
        return fig
    
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT
            c.descricao_canal,
            SUM(f.valor_total) AS total_vendas
        FROM
            DW_FINANCEIRO.FATO AS f
        JOIN
            DW_FINANCEIRO.CANAL AS c ON f.id_canal = c.id
        WHERE
            EXTRACT(YEAR FROM f.data_venda) = {ano_selecionado}
        GROUP BY
            c.descricao_canal
        ORDER BY
            total_vendas DESC;
        """
        cursor.execute(query)
        dados = cursor.fetchall()
        df_canais = pd.DataFrame(dados, columns=['descricao_canal', 'total_vendas'])
        
        # Se não houver dados, retorna um gráfico Plotly com uma mensagem de aviso
        if df_canais.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Nenhum dado de vendas por canal encontrado para o ano {ano_selecionado}.",
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title=f'Vendas por Canal no ano de {ano_selecionado}',
                              xaxis_visible=False, yaxis_visible=False)
            return fig
        
        # Cria o gráfico de pizza com Plotly Express
        fig = px.pie(
            df_canais,
            names='descricao_canal',
            values='total_vendas',
            title=f'Vendas por Canal no ano de {ano_selecionado}',
            color_discrete_sequence=px.colors.sequential.Agsunset,
            hole=0.4  # Para criar um gráfico de rosca
        )

        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(
            font=dict(family="Arial", size=12),
            height=500  # Ajusta a altura do gráfico
        )
        
        return fig
        
    except psycopg2.Error as e:
        print(f"Erro ao executar a consulta SQL: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao consultar dados: {e}",
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title='Erro', xaxis_visible=False, yaxis_visible=False)
        return fig
        
    finally:
        if conn:
            conn.close()

#==== Gráfico Gerado com Matplotlib ========

# def gerar_grafico_vendas_por_categoria(ano_selecionado):
#     conn = get_db_connection()
#     if conn is None:
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
#     try:
#         cursor = conn.cursor()
#         query = f"""
#         SELECT
#             cat.categoria,
#             SUM(f.qtde) AS total_quantidade
#         FROM
#             DW_FINANCEIRO.FATO AS f
#         JOIN
#             DW_FINANCEIRO.PRODUTO AS p ON f.id_produto = p.id
#         JOIN
#             DW_FINANCEIRO.SUBCATEGORIA AS sub ON p.id_subcategoria = sub.id
#         JOIN
#             DW_FINANCEIRO.CATEGORIA AS cat ON sub.id_categoria = cat.id
#         WHERE
#             EXTRACT(YEAR FROM f.data_venda) = {ano_selecionado}
#         GROUP BY
#             cat.categoria
#         ORDER BY
#             total_quantidade DESC;
#         """
#         cursor.execute(query)
#         dados = cursor.fetchall()
#         df_categorias = pd.DataFrame(dados, columns=['categoria', 'total_quantidade'])
#         if df_categorias.empty:
#             fig, ax = plt.subplots(figsize=(12, 6))
#             ax.text(0.5, 0.5, f"Nenhum dado de vendas por categoria encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
#             ax.axis('off')
#             return fig
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.bar(df_categorias['categoria'], df_categorias['total_quantidade'], color='green')
#         ax.set_xlabel('Categoria de Produto')
#         ax.set_ylabel('Quantidade Vendida')
#         ax.set_title(f'Quantidade Total de Vendas por Categoria de Produto no ano de {ano_selecionado}')
#         plt.xticks(rotation=45, ha='right')
#         plt.tight_layout()
#         return fig
#     except psycopg2.Error as e:
#         print(f"Erro ao executar a consulta SQL: {e}")
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.text(0.5, 0.5, f"Erro ao consultar dados: {e}", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
#     finally:
#         if conn:
#             conn.close()

#==== Gráfico Gerado com Plotly ========
def gerar_grafico_vendas_por_categoria(ano_selecionado):
    conn = get_db_connection()
    
    # Se houver erro de conexão, retorna um gráfico de erro do Plotly
    if conn is None:
        fig = go.Figure()
        fig.add_annotation(
            text="Erro ao conectar ao banco de dados.",
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title=f'Quantidade de Vendas por Categoria no ano de {ano_selecionado}',
                          xaxis_visible=False, yaxis_visible=False, height=500)
        return fig
    
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT
            cat.categoria,
            SUM(f.qtde) AS total_quantidade
        FROM
            DW_FINANCEIRO.FATO AS f
        JOIN
            DW_FINANCEIRO.PRODUTO AS p ON f.id_produto = p.id
        JOIN
            DW_FINANCEIRO.SUBCATEGORIA AS sub ON p.id_subcategoria = sub.id
        JOIN
            DW_FINANCEIRO.CATEGORIA AS cat ON sub.id_categoria = cat.id
        WHERE
            EXTRACT(YEAR FROM f.data_venda) = {ano_selecionado}
        GROUP BY
            cat.categoria
        ORDER BY
            total_quantidade DESC;
        """
        cursor.execute(query)
        dados = cursor.fetchall()
        df_categorias = pd.DataFrame(dados, columns=['categoria', 'total_quantidade'])
        
        # Se não houver dados, retorna um gráfico Plotly com uma mensagem de aviso
        if df_categorias.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Nenhum dado de vendas por categoria encontrado para o ano {ano_selecionado}.",
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title=f'Quantidade de Vendas por Categoria no ano de {ano_selecionado}',
                              xaxis_visible=False, yaxis_visible=False, height=500)
            return fig
        
        # Cria o gráfico de barras com Plotly Express
        fig = px.bar(
            df_categorias,
            x='categoria',
            y='total_quantidade',
            title=f'Quantidade Total de Vendas por Categoria no ano de {ano_selecionado}',
            labels={'categoria': 'Categoria de Produto', 'total_quantidade': 'Quantidade Vendida'},
            color='categoria', # Cor diferente para cada categoria
            color_continuous_scale=px.colors.sequential.Teal
        )
        
        fig.update_layout(
            xaxis_title='Categoria de Produto',
            yaxis_title='Quantidade Vendida',
            font=dict(family="Arial", size=12),
            height=500  # Ajusta a altura do gráfico
        )
        
        # Rotaciona os rótulos do eixo X
        fig.update_xaxes(tickangle=45)
        
        return fig
        
    except psycopg2.Error as e:
        print(f"Erro ao executar a consulta SQL: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao consultar dados: {e}",
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title='Erro', xaxis_visible=False, yaxis_visible=False, height=500)
        return fig
        
    finally:
        if conn:
            conn.close()

#==== Gráfico Gerado com Matplotlib ========

# def gerar_grafico_vendas_por_cidade(ano_selecionado):
#     conn = get_db_connection()
#     if conn is None:
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
#     try:
#         cursor = conn.cursor()
#         query = f"""
#         SELECT
#             cidade.cidade,
#             SUM(fato.valor_total) AS total_vendas
#         FROM
#             DW_FINANCEIRO.FATO AS fato
#         JOIN
#             DW_FINANCEIRO.CLIENTES AS clientes ON fato.id_cliente = clientes.id
#         JOIN
#             DW_FINANCEIRO.CIDADE AS cidade ON clientes.id_cidade = cidade.id
#         WHERE
#             EXTRACT(YEAR FROM fato.data_venda) = {ano_selecionado}
#         GROUP BY
#             cidade.cidade
#         ORDER BY
#             total_vendas DESC
#         LIMIT 10;
#         """
#         cursor.execute(query)
#         dados = cursor.fetchall()
#         df_cidades = pd.DataFrame(dados, columns=['cidade', 'total_vendas'])
#         if df_cidades.empty:
#             fig, ax = plt.subplots(figsize=(12, 6))
#             ax.text(0.5, 0.5, f"Nenhum dado de vendas por cidade encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
#             ax.axis('off')
#             return fig
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.bar(df_cidades['cidade'], df_cidades['total_vendas'], color='orange')
#         ax.set_xlabel('Cidade')
#         ax.set_ylabel('Total de Vendas')
#         ax.set_title(f'Top 10 Cidades com Maiores Vendas no ano de {ano_selecionado}')
#         plt.xticks(rotation=45, ha='right')
#         plt.tight_layout()
#         return fig
#     except psycopg2.Error as e:
#         print(f"Erro ao executar a consulta SQL: {e}")
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.text(0.5, 0.5, f"Erro ao consultar dados: {e}", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
#     finally:
#         if conn:
#             conn.close()

#===== Gráfico Gerado por Plotly =======
def gerar_grafico_vendas_por_cidade(ano_selecionado):
    conn = get_db_connection()
    
    # Em caso de erro de conexão, retorna um gráfico de erro do Plotly
    if conn is None:
        fig = go.Figure()
        fig.add_annotation(
            text="Erro ao conectar ao banco de dados.",
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title=f'Top 10 Cidades com Maiores Vendas no ano de {ano_selecionado}',
                          xaxis_visible=False, yaxis_visible=False, height=500)
        return fig
    
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT
            cidade.cidade,
            SUM(fato.valor_total) AS total_vendas
        FROM
            DW_FINANCEIRO.FATO AS fato
        JOIN
            DW_FINANCEIRO.CLIENTES AS clientes ON fato.id_cliente = clientes.id
        JOIN
            DW_FINANCEIRO.CIDADE AS cidade ON clientes.id_cidade = cidade.id
        WHERE
            EXTRACT(YEAR FROM fato.data_venda) = {ano_selecionado}
        GROUP BY
            cidade.cidade
        ORDER BY
            total_vendas DESC
        LIMIT 10;
        """
        cursor.execute(query)
        dados = cursor.fetchall()
        df_cidades = pd.DataFrame(dados, columns=['cidade', 'total_vendas'])
        
        # Se não houver dados, retorna um gráfico Plotly com uma mensagem de aviso
        if df_cidades.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Nenhum dado de vendas por cidade encontrado para o ano {ano_selecionado}.",
                xref="paper", yref="paper",
                showarrow=False,
                font=dict(size=16)
            )
            fig.update_layout(title=f'Top 10 Cidades com Maiores Vendas no ano de {ano_selecionado}',
                              xaxis_visible=False, yaxis_visible=False, height=500)
            return fig
        
        # Cria o gráfico de barras com Plotly Express
        fig = px.bar(
            df_cidades,
            x='cidade',
            y='total_vendas',
            title=f'Top 10 Cidades com Maiores Vendas no ano de {ano_selecionado}',
            labels={'cidade': 'Cidade', 'total_vendas': 'Total de Vendas'},
            color='cidade',
            color_continuous_scale=px.colors.sequential.Sunset
        )
        
        fig.update_layout(
            xaxis_title='Cidade',
            yaxis_title='Total de Vendas',
            font=dict(family="Arial", size=12),
            height=500
        )
        
        # Rotaciona os rótulos do eixo X
        fig.update_xaxes(tickangle=45)
        
        return fig
        
    except psycopg2.Error as e:
        print(f"Erro ao executar a consulta SQL: {e}")
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao consultar dados: {e}",
            xref="paper", yref="paper",
            showarrow=False,
            font=dict(size=16)
        )
        fig.update_layout(title='Erro', xaxis_visible=False, yaxis_visible=False, height=500)
        return fig
        
    finally:
        if conn:
            conn.close()
            
def gerar_grafico_faturamento_por_categoria(ano_selecionado, categorias_selecionadas):
    # Tratamento para caso o usuário não selecione nenhuma categoria
    if not categorias_selecionadas:
        fig = go.Figure()
        fig.add_annotation(
            text="Selecione uma ou mais categorias para a análise.",
            xref="paper", yref="paper", showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title='Selecione Categorias', xaxis_visible=False, yaxis_visible=False, height=500)
        return fig
    
    categorias_str = ", ".join([f"'{cat}'" for cat in categorias_selecionadas])
    
    conn = get_db_connection()
    if conn is None:
        # Erro de conexão com Plotly
        fig = go.Figure()
        fig.add_annotation(
            text="Erro ao conectar ao banco de dados.",
            xref="paper", yref="paper", showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title='Erro', xaxis_visible=False, yaxis_visible=False, height=500)
        return fig
        
    try:
        cursor = conn.cursor()
        query = f"""
        SELECT 
            cat.categoria,
            SUM(fato.valor_total) AS faturamento_bruto
        FROM
            DW_FINANCEIRO.FATO AS fato
        INNER JOIN
            DW_FINANCEIRO.PRODUTO AS prod ON fato.id_produto = prod.id
        INNER JOIN
            DW_FINANCEIRO.SUBCATEGORIA AS sub ON prod.id_subcategoria = sub.id
        INNER JOIN
            DW_FINANCEIRO.CATEGORIA AS cat ON sub.id_categoria = cat.id
        WHERE
            EXTRACT(YEAR FROM fato.data_venda) = {ano_selecionado}
            AND cat.categoria IN ({categorias_str})
        GROUP BY
            cat.categoria
        ORDER BY
            faturamento_bruto DESC
        """
        cursor.execute(query)
        dados = cursor.fetchall()
        df_categorias = pd.DataFrame(dados, columns=['categoria', 'faturamento_bruto'])
        
        if df_categorias.empty:
            fig = go.Figure()
            fig.add_annotation(
                text=f"Nenhum dado de categoria por faturamento bruto foi encontrado para o ano {ano_selecionado}.",
                xref="paper", yref="paper", showarrow=False, font=dict(size=12)
            )
            fig.update_layout(title='Dados Não Encontrados', xaxis_visible=False, yaxis_visible=False, height=500)
            return fig
            
        fig = px.bar(
            df_categorias,
            x='categoria',
            y='faturamento_bruto',
            title=f'Faturamento Bruto por Categoria no ano de {ano_selecionado}',
            labels={'categoria': 'Categoria', 'faturamento_bruto': 'Faturamento Bruto'},
            color_discrete_sequence=["#1faab4"]
        )
        
        fig.update_traces(
            textposition='outside',
            textfont_color='#222',
            textfont_weight='bold'
        )
        
        fig.update_layout(
            font=dict(size=12, color='#333'),
            title=dict(font=dict(size=16)),
            xaxis=dict(
                title_font=dict(size=14, color='#333', weight='bold'),
                tickfont=dict(color='#222', weight='bold')
            ),
            yaxis=dict(
                title_font=dict(size=14, color='#333', weight='bold'),
                tickfont=dict(color='#222')
            ),
            height=500
        )
        
        return fig
    
    except psycopg2.Error as e:
        print(f"Erro ao executar a consulta SQL: {e}")
        # Erro de consulta com Plotly
        fig = go.Figure()
        fig.add_annotation(
            text=f"Erro ao consultar dados: {e}",
            xref="paper", yref="paper", showarrow=False, font=dict(size=16)
        )
        fig.update_layout(title='Erro', xaxis_visible=False, yaxis_visible=False, height=500)
        return fig
        
    finally:
        if conn:
            conn.close()
            
# --- 3. Interface Gradio ---
def update_all_plots(ano_selecionado,categorias_selecionadas):
    return (
        gerar_grafico_vendas_por_mes_ano(ano_selecionado),
        gerar_grafico_vendas_por_canal(ano_selecionado),
        gerar_grafico_vendas_por_categoria(ano_selecionado),
        gerar_grafico_vendas_por_cidade(ano_selecionado),
        gerar_grafico_faturamento_por_categoria(ano_selecionado,categorias_selecionadas)
    )

def update_categoria_plot(ano_selecionado, categorias_selecionadas):
    return gerar_grafico_faturamento_por_categoria(ano_selecionado, categorias_selecionadas)

with gr.Blocks(title="Dashboard de Vendas DW Financeiro") as demo:
    gr.Markdown("# Dashboard de Vendas DW Financeiro")
    gr.Markdown("""
# 📊 Dashboard de Análise de Vendas

Bem-vindo ao meu projeto de dashboard interativo, criado para demonstrar a aplicação prática de conceitos de **Análise de Dados** e **Engenharia de Dados**.

Este projeto integra diversas tecnologias, desde o processamento dos dados até a visualização final:

* **ETL & Data Warehouse:** O processo de **Extração, Transformação e Carga (ETL)** foi realizado para alimentar um **Data Warehouse**, que serve como a base de dados centralizada e otimizada para análise.
* **Banco de Dados:** Os dados são acessados de um banco **PostgreSQL**, hospedado e gerenciado na plataforma **Render**.
* **Interface Web:** A interface amigável e interativa foi construída usando a biblioteca **Gradio**.
* **Visualização de Dados:** Todos os gráficos são gerados dinamicamente com a biblioteca **Plotly**, permitindo uma exploração detalhada e interativa dos dados de vendas.

Este dashboard é um estudo completo que une o backend de um Data Warehouse com uma incrível visualização web!
""")
    anos_disponiveis = get_anos_disponiveis()
    ano_padrao = anos_disponiveis[0] if anos_disponiveis else None
    
    categorias_disponiveis = get_categorias_disponiveis()
    # NOVO: Adiciona o filtro de ano
    with gr.Row():
        ano_dropdown = gr.Dropdown(anos_disponiveis, label="Selecione o Ano", value=ano_padrao, interactive=True)
    
    # --- NOVO: Adicionando as abas ---
    with gr.Tabs() as tabs:
        with gr.TabItem("Análise Geral"):
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Vendas Totais por Mês e Ano")
                    # O componente é criado e renderizado diretamente aqui
                    vendas_por_mes_plot = gr.Plot()
                with gr.Column():
                    gr.Markdown("### Vendas Totais por Canal")
                    vendas_por_canal_plot = gr.Plot()
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Quantidade de Vendas por Categoria de Produto")
                    vendas_por_categoria_plot = gr.Plot()
                with gr.Column():
                    gr.Markdown("### Top 10 Cidades com Maiores Vendas")
                    vendas_por_cidade_plot = gr.Plot()
        
        with gr.TabItem("Categorias"):
             # O Checkbox de "Selecionar Tudo"
            select_all_checkbox = gr.Checkbox(
                    label="Selecionar Todas as Categorias",
                    value=False
                )
            categorias_dropdown = gr.Dropdown(
                choices=categorias_disponiveis,
                label="Selecione a(s) Categoria(s)",
                multiselect=True,
                value=[categorias_disponiveis[0]] if categorias_disponiveis else []
                )
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Categoria por Faturamento Bruto")
                    categoria_por_faturamento_bruto = gr.Plot()
        with gr.TabItem("Assistente de Dados"):
            gr.Markdown("### Assitente IA para Consultas SQL")
            gr.Markdown("""Faça perguntas sobre os dados em linguagem natural. Exemplo: 'Quais foram as 5 cidades com mais vendas em 2024?'
                        
                        Esse é o esquema contido no Data Warehouse:

                        Tabelas:
                        - DW_FINANCEIRO.FATO (id, data_venda, data_entrega, id_canal, id_cliente, id_produto, qtde, valor_total)
                        - DW_FINANCEIRO.MARCA (id, marca)
                        - DW_FINANCEIRO.CATEGORIA (id, categoria)
                        - DW_FINANCEIRO.CANAL (id, descricao_canal)
                        - DW_FINANCEIRO.CLIENTES (id, nome, sobrenome, data_nascimento, estado_civil, genero, educacao, id_cidade)
                        - DW_FINANCEIRO.CIDADE (id, cidade, uf)
                        - DW_FINANCEIRO.PRODUTO (id, descricao_produto, id_subcategoria, id_marca, preco_unitario, tributos, custo)
                        - DW_FINANCEIRO.SUBCATEGORIA (id, subcategoria, id_categoria)

                        Relacionamentos:
                        - DW_FINANCEIRO.FATO.id_canal -> DW_FINANCEIRO.CANAL.id
                        - DW_FINANCEIRO.FATO.id_cliente -> DW_FINANCEIRO.CLIENTES.id
                        - DW_FINANCEIRO.FATO.id_produto -> DW_FINANCEIRO.PRODUTO.id
                        - DW_FINANCEIRO.CLIENTES.id_cidade -> DW_FINANCEIRO.CIDADE.id
                        - DW_FINANCEIRO.PRODUTO.id_marca -> DW_FINANCEIRO.MARCA.id
                        - DW_FINANCEIRO.PRODUTO.id_subcategoria -> DW_FINANCEIRO.SUBCATEGORIA.id
                        - DW_FINANCEIRO.SUBCATEGORIA.id_categoria -> DW_FINANCEIRO.CATEGORIA.id
                                                """)
            
            pergunta_box = gr.Textbox(label="Faça uma Pergunta:")
            
            with gr.Row():
                executar_btn = gr.Button("Executar Consulta")
                limpar_btn = gr.Button("Limpar")
                
            resultado_box = gr.Textbox(label="Resultado da Consulta:")
            
            executar_btn.click(
                fn=execute_ai_query,
                inputs=pergunta_box,
                outputs=resultado_box
            )
            
            limpar_btn.click(
                fn=lambda: "",
                inputs=None,
                outputs=resultado_box
            )

    # Saídas para a aba de Análise Geral
    all_outputs = [
        vendas_por_mes_plot,
        vendas_por_canal_plot,
        vendas_por_categoria_plot,
        vendas_por_cidade_plot,
        categoria_por_faturamento_bruto
    ]
    
    # Saídas para a aba de Categorias (apenas um gráfico)
    categoria_output = [categoria_por_faturamento_bruto]

    # Conecta a função de atualização a ambos os dropdowns
    # O dropdown de ano atualiza TODOS os gráficos
    ano_dropdown.change(
        fn=update_all_plots,
        inputs=[ano_dropdown, categorias_dropdown],
        outputs=all_outputs
    )
    
    # O checkbox atualiza o dropdown
    select_all_checkbox.change(
        fn=handle_select_all_categories,
        inputs=[select_all_checkbox, gr.State(categorias_disponiveis), categorias_dropdown],
        outputs=categorias_dropdown
    )
    # O dropdown de categorias agora atualiza APENAS o gráfico de categoria
    categorias_dropdown.change(
        fn=update_categoria_plot,
        inputs=[ano_dropdown, categorias_dropdown],
        outputs=categoria_output # Note que a saída é só o gráfico desta aba
    )

    # Inicializa todos os gráficos ao carregar a página
    demo.load(
        fn=update_all_plots,
        inputs=[ano_dropdown, categorias_dropdown],
        outputs=all_outputs
    )

demo.launch()