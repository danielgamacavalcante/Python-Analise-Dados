# # app.py

# import gradio as gr
# import pandas as pd
# import psycopg2
# import matplotlib.pyplot as plt
# import os
# from io import BytesIO
# import base64

# # --- 1. Configurações do Banco de Dados ---
# DB_HOST = "localhost"
# DB_NAME = "db_financeiro"
# DB_USER = "postgres"
# DB_PASSWORD = "1234"
# DB_PORT = "5432"

# def get_db_connection():
#     try:
#         conn = psycopg2.connect(
#             host=DB_HOST,
#             database=DB_NAME,
#             user=DB_USER,
#             password=DB_PASSWORD,
#             port=DB_PORT
#         )
#         return conn
#     except Exception as e:
#         print(f"Erro ao conectar ao banco de dados: {e}")
#         return None

# # Função para obter a lista de anos disponíveis para o filtro
# def get_anos_disponiveis():
#     conn = get_db_connection()
#     if conn is None:
#         return []
#     try:
#         cursor = conn.cursor()
#         query = """
#         SELECT DISTINCT EXTRACT(YEAR FROM data_venda) AS ano
#         FROM DW_FINANCEIRO.FATO
#         ORDER BY ano DESC;
#         """
#         cursor.execute(query)
#         anos = [str(ano[0]) for ano in cursor.fetchall()]
#         return anos
#     except Exception as e:
#         print(f"Erro ao obter anos disponíveis: {e}")
#         return []
#     finally:
#         if conn:
#             conn.close()

# # --- 2. Funções para Gerar Gráficos (TODAS AGORA ACEITAM O FILTRO DE ANO) ---

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

# def gerar_grafico_vendas_por_canal(ano_selecionado):
#     conn = get_db_connection()
#     if conn is None:
#         fig, ax = plt.subplots(figsize=(8, 8))
#         ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
    
#     try:
#         cursor = conn.cursor()
#         # Adicionado WHERE para filtrar por ano
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

# def gerar_grafico_vendas_por_categoria(ano_selecionado):
#     conn = get_db_connection()
#     if conn is None:
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
    
#     try:
#         cursor = conn.cursor()
#         # Adicionado WHERE para filtrar por ano
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

# def gerar_grafico_vendas_por_cidade(ano_selecionado):
#     conn = get_db_connection()
#     if conn is None:
#         fig, ax = plt.subplots(figsize=(12, 6))
#         ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
#         ax.axis('off')
#         return fig
    
#     try:
#         cursor = conn.cursor()
#         # Adicionado WHERE para filtrar por ano
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


# # --- 3. Interface Gradio ---
# def update_all_plots(ano_selecionado):
#     # Esta função chama todas as outras funções de gráfico
#     # e retorna suas saídas para o Gradio
#     return (
#         gerar_grafico_vendas_por_mes_ano(ano_selecionado),
#         gerar_grafico_vendas_por_canal(ano_selecionado),
#         gerar_grafico_vendas_por_categoria(ano_selecionado),
#         gerar_grafico_vendas_por_cidade(ano_selecionado)
#     )

# with gr.Blocks(title="Dashboard de Vendas DW Financeiro") as demo:
#     gr.Markdown("# Dashboard de Vendas DW Financeiro")
#     gr.Markdown("Visualize os principais indicadores do seu Data Warehouse de Finanças.")

#     # Obter os anos disponíveis para o dropdown
#     anos_disponiveis = get_anos_disponiveis()
#     ano_padrao = anos_disponiveis[0] if anos_disponiveis else None

#     # NOVO: Adiciona o filtro de ano
#     with gr.Row():
#         ano_dropdown = gr.Dropdown(anos_disponiveis, label="Selecione o Ano", value=ano_padrao, interactive=True)

#     with gr.Row():
#         with gr.Column():
#             gr.Markdown("### Vendas Totais por Mês e Ano")
#             vendas_por_mes_plot = gr.Plot(label="Gráfico de Vendas por Mês/Ano")

#         with gr.Column():
#             gr.Markdown("### Vendas Totais por Canal")
#             vendas_por_canal_plot = gr.Plot(label="Gráfico de Vendas por Canal")

#     with gr.Row():
#         with gr.Column():
#             gr.Markdown("### Quantidade de Vendas por Categoria de Produto")
#             vendas_por_categoria_plot = gr.Plot(label="Gráfico de Quantidade por Categoria")
#         with gr.Column():
#             gr.Markdown("### Top 10 Cidades com Maiores Vendas")
#             vendas_por_cidade_plot = gr.Plot(label="Gráfico de Vendas por Cidade")
            
#     # Criamos uma tupla com todos os outputs
#     all_outputs = (vendas_por_mes_plot, vendas_por_canal_plot, vendas_por_categoria_plot, vendas_por_cidade_plot)
    
#     # Adicionamos uma nova interatividade: quando o ano mudar,
#     # a função update_all_plots() é chamada e atualiza todos os gráficos de uma vez.
#     ano_dropdown.change(
#         fn=update_all_plots,
#         inputs=ano_dropdown,
#         outputs=all_outputs
#     )
    
#     # Inicializa todos os gráficos ao carregar a página
#     demo.load(fn=lambda: update_all_plots(ano_padrao), inputs=None, outputs=all_outputs)

# demo.launch()
# app.py

# app.py

import gradio as gr
import pandas as pd
import psycopg2
import matplotlib.pyplot as plt
import os
from io import BytesIO
import base64

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

def gerar_grafico_vendas_por_mes_ano(ano_selecionado):
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
        if df_vendas.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f"Nenhum dado encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(df_vendas['mes'], df_vendas['total_vendas'], color='skyblue')
        ax.set_xlabel('Mês')
        ax.set_ylabel('Total de Vendas')
        ax.set_title(f'Total de Vendas no ano de {ano_selecionado}')
        plt.tight_layout()
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

def gerar_grafico_vendas_por_canal(ano_selecionado):
    conn = get_db_connection()
    if conn is None:
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.5, 0.5, "Erro ao conectar ao banco de dados.", ha='center', va='center', fontsize=12)
        ax.axis('off')
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
        if df_canais.empty:
            fig, ax = plt.subplots(figsize=(8, 8))
            ax.text(0.5, 0.5, f"Nenhum dado de vendas por canal encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.pie(df_canais['total_vendas'], labels=df_canais['descricao_canal'], autopct='%1.1f%%', startangle=90)
        ax.set_title(f'Vendas por Canal no ano de {ano_selecionado}')
        plt.tight_layout()
        return fig
    except psycopg2.Error as e:
        print(f"Erro ao executar a consulta SQL: {e}")
        fig, ax = plt.subplots(figsize=(8, 8))
        ax.text(0.5, 0.5, f"Erro ao consultar dados: {e}", ha='center', va='center', fontsize=12)
        ax.axis('off')
        return fig
    finally:
        if conn:
            conn.close()

def gerar_grafico_vendas_por_categoria(ano_selecionado):
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
        if df_categorias.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f"Nenhum dado de vendas por categoria encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(df_categorias['categoria'], df_categorias['total_quantidade'], color='green')
        ax.set_xlabel('Categoria de Produto')
        ax.set_ylabel('Quantidade Vendida')
        ax.set_title(f'Quantidade Total de Vendas por Categoria de Produto no ano de {ano_selecionado}')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
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

def gerar_grafico_vendas_por_cidade(ano_selecionado):
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
        if df_cidades.empty:
            fig, ax = plt.subplots(figsize=(12, 6))
            ax.text(0.5, 0.5, f"Nenhum dado de vendas por cidade encontrado para o ano {ano_selecionado}.", ha='center', va='center', fontsize=12)
            ax.axis('off')
            return fig
        fig, ax = plt.subplots(figsize=(12, 6))
        ax.bar(df_cidades['cidade'], df_cidades['total_vendas'], color='orange')
        ax.set_xlabel('Cidade')
        ax.set_ylabel('Total de Vendas')
        ax.set_title(f'Top 10 Cidades com Maiores Vendas no ano de {ano_selecionado}')
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
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
        gerar_grafico_vendas_por_cidade(ano_selecionado)
    )

with gr.Blocks(title="Dashboard de Vendas DW Financeiro") as demo:
    gr.Markdown("# Dashboard de Vendas DW Financeiro")
    gr.Markdown("Visualize os principais indicadores do seu Data Warehouse de Finanças.")

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
        
        with gr.TabItem("Nova Aba (Exemplo)"):
            gr.Markdown("## Conteúdo para uma nova aba")
            gr.Markdown("Você pode adicionar novos gráficos, tabelas ou análises aqui.")

    all_outputs = (vendas_por_mes_plot, vendas_por_canal_plot, vendas_por_categoria_plot, vendas_por_cidade_plot)
    
    # Configura a interatividade
    ano_dropdown.change(
        fn=update_all_plots,
        inputs=ano_dropdown,
        outputs=all_outputs
    )
    
    # Inicializa todos os gráficos
    demo.load(fn=lambda: update_all_plots(ano_padrao), inputs=None, outputs=all_outputs)

demo.launch()