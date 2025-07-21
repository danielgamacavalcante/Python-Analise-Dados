import os
import shutil
import time
import schedule
import pandas as pd
import win32com.client as win32
from schedule import repeat,every
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory


#==============================================FUNÇÕES de LEITURA DE PASTA E ARQUIVO=============================

def obter_caminho_arquivo():
    """
    Função para obter o caminho completo de um arquivo selecionado pelo usuário.

    Retorna:
        str: O caminho completo do arquivo selecionado, ou None se nenhum arquivo for escolhido.
    """

    root = Tk()
    root.withdraw()  # Esconde a janela principal

    # Abre uma janela para o usuário selecionar o arquivo
    print("SELECIONE UM ARQUIVO!!")
    try:
        file_path = askopenfilename()
        return file_path
    except FileNotFoundError:
        print("Não foi possível encontrar o arquivo. Verifique o caminho e tente novamente.")
    except Exception as e:
        print(f'Ocorreu um erro: {e} ')


#lista o que está dentro de uma pasta
def listar_arquivos_diretorio(caminho_do_arquivo):
    print('Arquivos do Diretório: ')
    for arquivo in os.listdir(caminho_do_arquivo):
        print(arquivo)
#percorrer um arquivo selecionado, com tratativas de possíveis erros.
def percorrer_arquivo_selecionado(caminho_do_arquivo):
    try:
        with open(caminho_do_arquivo, encoding='utf-8') as arquivo:
            for linha in arquivo:
                print(linha, end='')
    except FileNotFoundError:
        print("Não foi possível encontrar o arquivo. Verifique o caminho e tente novamente.")
    except UnicodeDecodeError:
        print("Erro ao decodificar o arquivo. Verifique a codificação.")
    except Exception as e:  # Captura outras exceções
        print(f"Ocorreu um erro inesperado: {e}")

#mostra o caminho do diretório, após selecionar um determinado arquivo contido neste diretório.
def mostrar_caminho_diretorio(caminho_do_arquivo):
        caminho_do_diretorio = os.path.dirname(caminho_do_arquivo)
        print(caminho_do_diretorio)

#usuário seleciona diretório e com isso consegue o seu caminho na variável caminho_do_diretorio
def selecionando_diretorio():
    janela_padrao = Tk().withdraw()
    caminho_do_diretorio = askdirectory()
    print("SELECIONE UM Diretório!!")
    if caminho_do_diretorio:
        return caminho_do_diretorio
    else:
        print('Nenhum diretório selecionado.')

#usuário seleciona um arquivo txt ou csv e com isso consegue extrair certas inforamções de outras funções.
def selecionando_arquivo_txt_csv():
    janela_padrao = Tk().withdraw()
    caminho_do_arquivo = askopenfilename(filetypes=(("Arquivos de texto", "*.txt"), ("Arquivos csv", "*.csv")))

    if caminho_do_arquivo:
        mostrar_caminho_diretorio(caminho_do_arquivo)

    else:
        print("Nenhum arquivo selecionado")

#passa o caminho de um ARQUIVO completo e copia esse arquivo dentro de outro DIRETÓRIO

def copiar_arquivo(caminho_origem_arquivo, caminho_destino_pasta):
    """Copia um arquivo de um local para outro."""

    # Verifica se o arquivo de origem existe
    if not os.path.exists(caminho_origem_arquivo):
        print("Arquivo não encontrado.")
        return

    # Copia o arquivo
    try:
        shutil.copy(caminho_origem_arquivo, caminho_destino_pasta)
        print("Arquivo copiado com sucesso!")
        #retorna o caminho do novo arquivo copiado com sua extensão
        return f'{caminho_destino_pasta}\\{os.path.basename(caminho_origem_arquivo)}'
    except shutil.Error as e:
        print(f"Erro ao copiar o arquivo: {e}")

def faz_backup(caminho_origem_arquivo,caminho_destino_pasta):
    #verifica se o arquivo de origem existe
    if not os.path.exists(caminho_origem_arquivo):
        print("Arquivo não encontrado.")
        return

    # Obtém o nome do arquivo original sem a extensão
    nome_arquivo, extensao = os.path.splitext(os.path.basename(caminho_origem_arquivo))

    # Cria o novo nome do arquivo com a data
    novo_nome = f"{nome_arquivo}_backup{extensao}"
    caminho_destino_completo = os.path.join(caminho_destino_pasta, novo_nome)

    # Copia o arquivo para o novo local com o novo nome
    try:
        shutil.copy(caminho_origem_arquivo, caminho_destino_completo)
        print(f"Arquivo copiado e renomeado para: {novo_nome}")
    except shutil.Error as e:
        print(f"Erro ao copiar o arquivo: {e}")

#========================================================================================TAREFAS==================================================


@repeat(every().day.at('10:56:50'))
def tarefa():
    nome_arquivo = copiar_arquivo(r'C:/Users/Win 10 Pro/Documents/Bases/Dimensão/Produto.xlsx',r'C:/Users/Win 10 Pro/Documents/MEU DOCUMENTOS/CURSOS GERAIS/COMPUTAÇÃO/Web')
    faz_backup(nome_arquivo, r'C:\Users\Win 10 Pro\Documents\MEU DOCUMENTOS\CURSOS GERAIS\COMPUTAÇÃO\Web\backups')



@repeat(every().day.at('10:58:00'))
def tarefa2():
    print('Iniciou TAREFA2!!!')
#CONFIG EMAIL
    lista_emails = []
    # importa e-mails
    # os emails que estão contidos em emails.txt são importados para o excel base_emails.xlsx
    # Obs: Atualizar emails dentro de emails.txt colocando abaixo do emails existente e abrir base_emails.xlsx para atualizar o excel
    emails = pd.read_excel('C:/Users/Win 10 Pro/Documents/MEU DOCUMENTOS/CURSOS GERAIS/COMPUTAÇÃO/Python/pycharm/automacaoExcelFaturaLoja/emails/base_emails.xlsx')

    # pega somente a coluna com o título, escrito no excel, como Nome
    # .itertuples() percorrer as linhas de uma tabela
    for email in emails.itertuples(index=False):
        lista_emails.append(email.Column1)

    # só para percorrer e ver o que está dentro da lista
    # for i in lista_emails:
    #     print(i)

#===================================JUNTAR PLANILHAS EXCEL==================================================================#
#PEGA AS TABELAS A PARTIR DA 5 LINHA DE CADA TABELA,  QUE ESTÃO DENTRO DO CAMINHO FATO e JUNTA EM UMA ÚNICA TABELA
    #Caminho para a pasta com os arquivos
    pasta = r'C:\Users\Win 10 Pro\Documents\Bases\Fato'

    #lista com todos os arquivos dentro da pasta
    arquivos = [os.path.join(pasta,arquivo) for arquivo in os.listdir(pasta)]

    #tabela começa vazia
    tabela_final = pd.DataFrame()

    #loop para iterar sobre todos os arquivos
    #e ir juntando as informações na "tabale_final"
    for arquivo in arquivos:
        #ler arquivo excel pulando 4 linhas
        df = pd.read_excel(arquivo, skiprows=4)
    #junta informações do arquivo na tabela
    tabela_final= pd.concat([tabela_final,df])

    #exporta tabela para uma planilha excel
    tabela_final.to_excel("dados_completos.xlsx")
    print(tabela_final)
    ##################################### FIM DE JUNÇÃO(CONCATENAÇÃO) de TABELAS###################################################

    ####################################### TRATAMENTO DE TABELAS #################################################################
    #ler tabela pelo caminho
    #tabela_produto = pd.read_excel('C:/Users/Win 10 Pro/Documents/Bases/Dimensão/Produto.xlsx')
    tabela_produto = pd.read_excel(r'C:/Users/Win 10 Pro/Documents/MEU DOCUMENTOS/CURSOS GERAIS/COMPUTAÇÃO/Web/Produto.xlsx')
    #pega coluna ID_Produto e Qtde e agrupa pelo ID_Produto somando tudo, repete com o Preco Unitário
    quantidade = tabela_final[['ID_Produto','Qtde']].groupby('ID_Produto').sum()
    preco_unitario = tabela_produto[['ID_Produto','Preco_Unitario']].groupby('ID_Produto').sum()

    #criando uma tabela com to_frame(); com o Faturamento Bruto advindo da quantidade * preco unitario
    tab_fat_bruto = (quantidade['Qtde'] * preco_unitario['Preco_Unitario']).to_frame()

    #renomeia a coluna 0 para Faturamento Total
    tab_fat_bruto = tab_fat_bruto.rename(columns={0:'Faturamento Total'})
    print(tab_fat_bruto)
    ###################################### FIM DE TRATAMENTO TABELAS #############################################################
    for contato in lista_emails:
        appOutlook = win32.Dispatch('outlook.application')
        email = appOutlook.CreateItem(0)
        email.To = str(contato)

        email.Subject = 'Relatório das lojas'
        # Corpo do Email é feito em HTML, nele temos a conversão das colunas selecionadas em formato de planilha HTML(to_html)
        # Depois formatamos(formatters) as colunas com dinheiro colocando o R$ e 2 casas decimais (.2f)
        email.HTMLBody = f'''
        <p>Prezados,</p>

        <p>Segue relatório de Vendas por cada Loja.</p>

        <p><strong>Faturamento:</strong></p>
        {preco_unitario.to_html(formatters={'Preco_Unitario': 'R${:,.2f}'.format})}

        <p><strong>Quantidade Vendida:</strong></p>
        {quantidade.to_html()}

        <p><strong>Faturamento Total de Produtos em cada Loja:</strong></p>
        {tab_fat_bruto.to_html(formatters={'Faturamento Total': 'R${:,.2f}'.format})}

        <p>Qualquer dúvida estou à disposição.</p>
        <p>Att.,</p>
        <p>Daniel G.</p>
        '''

        email.Send()
        time.sleep(1)

#=============================================================================================================================
#=============================================================================================================================
#=============================================================================================================================
# caminho_do_arquivo = obter_caminho_arquivo()
# caminho_do_diretorio = selecionando_diretorio()
# copiar_arquivo(caminho_do_arquivo,caminho_do_diretorio)
#=============pode passar o caminho direto===================================================================================
# copiar_arquivo('escreva_caminho_do_arquivo ex: c:documentos/codigo/sql/select.txt','escreva o caminho do diretorio ex: C:/documentos/Web')

while True:
    # run_pending()  fica escutando as tarefas de schedule que e executa elas quando é atingida seu parametro.
    schedule.run_pending()
    time.sleep(1)



