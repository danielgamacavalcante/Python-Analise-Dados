import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from tkinter import Tk
from tkinter.filedialog import askopenfilename, askdirectory


#usuário seleciona diretório e com isso consegue o seu caminho na variável caminho_do_diretorio
def selecionando_diretorio():
    janela_padrao = Tk().withdraw()
    caminho_do_diretorio = askdirectory()
    print("SELECIONE UM Diretório!!")
    if caminho_do_diretorio:
        return caminho_do_diretorio
    else:
        print('Nenhum diretório selecionado.')

pasta = selecionando_diretorio()
print(f"Caminho:{pasta}")

#===================================JUNTAR PLANILHAS EXCEL==================================================================#
if pasta:
    #lista com todos os arquivos dentro da pasta
    arquivos = [os.path.join(pasta,arquivo) for arquivo in os.listdir(pasta) if arquivo.endswith('.csv')]

    #tabela começa vazia
    tabela_final = pd.DataFrame()
    #comando para destravar a exibição de todas as colunas e linhas
    pd.set_option('display.max_columns',None)
    # pd.set_option('display.max_rows',None)

    #loop para iterar sobre todos os arquivos
    #e ir juntando as informações na "tabale_final"
    for arquivo in arquivos:
        try:
            df = pd.read_csv(
                    arquivo,
                    encoding='Windows-1252',
                    sep=';')
            #junta informações do arquivo na tabela
            tabela_final= pd.concat([tabela_final,df],ignore_index=True)
        except Exception as e:
            print(f"Não foi possível processar o arquivo {arquivo}: {e}")
    
        #exporta tabela para uma planilha csv
    tabela_final.to_csv("dados_completos.csv",index=False)
    print('Fim do Merge de Arquivos CSV!!')
    ##################################### FIM DE JUNÇÃO(CONCATENAÇÃO) de TABELAS###################################################

    print(f"\nTotal de linhas nos dados combinados: {len(tabela_final)}")
    print(f'\nHeader dados_completos:\n{tabela_final.head()}')


    #mostra linhas finais da base de dados
    print("\n\n=================== Linhas finais:\n")
    print(tabela_final.tail())

    
    #avalia max e min de data_inversa
    inicio = pd.to_datetime(tabela_final['data_inversa']).dt.date.min()
    fim = pd.to_datetime(tabela_final['data_inversa']).dt.date.max()
    print("\n\nPeríodo Vendas:\n")
    print('Período das Vendas - De: ',inicio,' Até:',fim)

    print('\n\n==================================Pega Mediana de mortos\n')
    #pega a mediana do mortos
    tabela_final['mortos'] = tabela_final['mortos'].astype(pd.Int64Dtype())
    mediana_mortos = tabela_final.loc[:,'mortos'].median()
    print('Mediana: ',mediana_mortos)

    print('\n\n==================================Pega Mediana de feridos_leves\n')
    #pega a mediana do feridos_leves
    tabela_final['feridos_leves'] = tabela_final['feridos_leves'].astype(pd.Int64Dtype())
    mediana_leves = tabela_final.loc[:,'feridos_leves'].median()
    print('Mediana: ',mediana_leves)

    print('\n\n==================================Pega Mediana de feridos_graves\n')
    #pega a mediana do feridos_graves
    tabela_final['feridos_graves'] = tabela_final['feridos_graves'].astype(pd.Int64Dtype())
    mediana_graves = tabela_final.loc[:,'feridos_graves'].median()
    print('Mediana: ',mediana_graves)

    print('\n\n==================================Pega Mediana de idade\n')
    #pega a mediana do feridos_graves
    tabela_final['idade'] = tabela_final['idade'].astype(pd.Int64Dtype())
    mediana_idade = tabela_final.loc[:,'idade'].median()
    print('Mediana: ',mediana_idade)

    print(tabela_final.info())

    #verifica se existe dados nulos
    print('====================Dados Nulos:\n',tabela_final.isnull().sum())

    #caso tenha valores null um exemplo para corrigir este valor seria assim:
    # df_dados['Preço Unitário'] = df_dados['Preço Unitário'].fillna((df_dados['Preço Unitário'].median()))
    #=========================PLOT DE GRÁFICO=====================================
    #apenas de colunas que possuam número, por isso, utilizamos int e float
    print('\n\nPega os nomes das colunas do tipo int64 e float64:\n')
    variaveis_numericas = []

    for i in tabela_final.columns[0:48].tolist():
        if tabela_final.dtypes[i] == 'int64' or tabela_final.dtypes[i] == 'float64':
            #printa as colunas do tipo int64 e float64
            print(i,' : ',tabela_final.dtypes[i])
            #armazena os nomes das colunas em uma lista
            variaveis_numericas.append(i)

    print('\n\n',variaveis_numericas,'\n')


    plt.rcParams['figure.figsize'] = [12.00,14.00] #configura tamanho da tela
    plt.rcParams['figure.autolayout'] = True #coloca o layout como auto

    f, axes = plt.subplots(4,2) #4 linhas e 2 colunas

    linha = 0
    coluna = 0

    for i in variaveis_numericas:
        sns.boxplot(data = tabela_final, y=i, ax=axes[linha][coluna])
        coluna +=1
        if coluna == 2:
            linha +=1
            coluna=0

    plt.show() #mostra o gráfico

    #=============PEGA SOMENTE idade COM VALOR MAIOR 110 ordenados do menor para o maior===========
    print("=============PEGA SOMENTE idade COM VALOR MAIOR 110 ordenados do menor para o maior===========")
    idade_discrepante = tabela_final.loc[tabela_final['idade'] > 110].sort_values(by='idade', ascending=True)
    print(idade_discrepante,'\n Total idade > 110:',idade_discrepante.count())

    #================Troca as idades maiores de 110 para a mediana de idade no valor de 37=====================
    valor_med_idade = tabela_final['idade'].median()
    print('Valor Média de Idade: ',valor_med_idade)

    tabela_final.loc[tabela_final['idade'] > 100, 'idade'] = valor_med_idade
    print(f"Valores de 'idade' maiores que 110 foram substituídos pela mediana ({valor_med_idade}).")

    print("\nVerificando idades após a substituição:")
    print(tabela_final.loc[tabela_final['idade'] > 110]) 
    # ---

    ### Plotando o Boxplot de 'idade' após o tratamento

    # ```python
    plt.figure(figsize=(8, 6)) # Define o tamanho da figura para este gráfico específico
    sns.boxplot(data=tabela_final, y='idade')
    plt.title('Distribuição da Idade (Após Tratamento de Outliers)') # Adiciona um título ao gráfico
    plt.ylabel('Idade') # Rótulo do eixo Y
    plt.show() # Mostra o gráfico da idade
    # ```

    # ---



    exit()


arquivo_merge = pd.read_csv('dados_completos.csv',dtype=str) 
print(f"\nTotal de linhas nos dados combinados: {len(arquivo_merge)}")
print(arquivo_merge.head())

