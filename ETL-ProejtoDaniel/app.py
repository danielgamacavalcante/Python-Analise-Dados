# app.py
import gradio as gr
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import os
from io import BytesIO
import base64
import plotly.express as px
import plotly.graph_objects as go

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
            
def gerar_grafico_faturamento_por_categoria(ano_selecionado):
    conn = get_db_connection()
    if conn is None:
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
        ax.axis('off')
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
        GROUP BY
            cat.categoria
        ORDER BY
            faturamento_bruto DESC
        """
        cursor.execute(query)
        dados = cursor.fetchall()
        df_categorias = pd.DataFrame(dados, columns=['categoria', 'faturamento_bruto'])
        if df_categorias.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f"Nenhum dado de categoria por faturamento bruto foi encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig
        fig = px.bar(
            df_categorias,
            x='categoria',
            y='faturamento_bruto',
            title=f'Categorias por Faturamento Bruto no ano de {ano_selecionado}',
            labels={'categoria': 'Categoria', 'faturamento_bruto': 'Faturamento Bruto'},
            color_discrete_sequence=["#1faab4"] # Define a cor das barras
        )
        
        # --- NOVO CÓDIGO: Formata o texto das barras (negrito, cor, posição) ---
        fig.update_traces(
            textposition='outside', # Posição do texto: pode ser 'inside' ou 'outside'
            textfont_color='#222',  # Cor do texto
            textfont_weight='bold'  # Texto em negrito
        )
        
        fig.update_layout(
            font=dict(size=12, color='#333'), # Escurece o texto geral e do tooltip
            title=dict(font=dict(size=16)),
            xaxis=dict(
                title_font=dict(size=14, color='#333', weight='bold'),
                tickfont=dict(color='#222', weight='bold')  # Escurece os rótulos do eixo X (categorias)
            ),
            yaxis=dict(
                title_font=dict(size=14, color='#333', weight='bold'),
                tickfont=dict(color='#222')  # Escurece os rótulos do eixo Y (valores)
            )
        )
        return fig
    except psycopg2.Error as e:
        print(f"Erro ao executar a consulta SQL: {e}")
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.text(0.5, 0.5, f"Erro ao consultar dados: {e}", ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig
    finally:
        if conn:
            conn.close()
            
# --- 3. Interface Gradio ---
def update_all_plots(ano_selecionado):
    return (
        gerar_grafico_vendas_por_mes_ano(ano_selecionado),
        gerar_grafico_vendas_por_canal(ano_selecionado),
        gerar_grafico_vendas_por_categoria(ano_selecionado),
        gerar_grafico_vendas_por_cidade(ano_selecionado),
        gerar_grafico_faturamento_por_categoria(ano_selecionado)
    )

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
            with gr.Row():
                with gr.Column():
                    gr.Markdown("### Categoria por Faturamento Bruto")
                    categoria_por_faturamento_bruto = gr.Plot()

    all_outputs = (vendas_por_mes_plot, vendas_por_canal_plot, vendas_por_categoria_plot, vendas_por_cidade_plot,categoria_por_faturamento_bruto )
    
    # Configura a interatividade
    ano_dropdown.change(
        fn=update_all_plots,
        inputs=ano_dropdown,
        outputs=all_outputs
    )
    
    # Inicializa todos os gráficos
    demo.load(fn=lambda: update_all_plots(ano_padrao), inputs=None, outputs=all_outputs)

demo.launch()