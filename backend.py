# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 17:56:31 2025

@author: Marco Marques de Castro
"""

# Importação de bibliotecas
import pandas as pd
import numpy as np

"""
Definindo função para coletar dados da planilha de controle
"""
def coleta_controle(controle) :
    
    # Lendo planilha de controle
    planilha_controle = pd.ExcelFile(controle)
    
    # Criando lista com as corretoras
    corretoras = ["BTG", "XP", "Ágora"]
    
    # Criando lista para armazenar os data frames
    dataframes = []
    
    # Iteração para pegar colunas específicas de cada planilha de cada corretora
    for c in corretoras :
        
        # Lendo planilha por corretora e selecionando colunas específicas
        planilha = planilha_controle.parse(c, skiprows=1, skipfooter=5, usecols=["Conta", "Cliente", 
                                                                                 "Corretora", "Operador",
                                                                                 "Status", "Carteira", 
                                                                                 "Observações", "Situação"])
        # Adicionando data frame a lista 
        dataframes.append(planilha)
        
    # Criando data frame agregado
    df_agregado = pd.concat(dataframes, ignore_index=True)  
    
    return df_agregado 
        
"""
Definindo função para gerar divisão do BTG
"""
def divisao_btg(saldo_btg, pl_btg) :
    
    # Lendo arquivos de saldo e pl respectivamente
    saldobtg = pd.read_excel(saldo_btg, usecols=["Conta", "Saldo"], skipfooter=2)
    plbtg = pd.read_excel(pl_btg, usecols=["Conta", "Valor"], skipfooter=2)
    
    # Realizando join com os data frames de saldo e pl
    df_saldo_btg = saldobtg.merge(plbtg, on="Conta", how="outer")
    
    return df_saldo_btg
    
"""
Definindo função para gerar divisão da XP
"""
def divisao_xp(saldo_xp) :
    
    # Lendo arquivo de saldo xp
    saldoxp = pd.read_excel(saldo_xp, usecols=["COD. CLIENTE", "PATRIMÔNIO TOTAL", "D0"])
    
    # Mudando o nome da coluna 'COD.CLIENTE', 'PATRIMÔNIO TOTAL' e 'D0' para 'Conta', 'Valor', 'Saldo'
    mapper = {"COD. CLIENTE" : "Conta", "PATRIMÔNIO TOTAL" : "Valor", "D0" : "Saldo"}
    saldoxp = saldoxp.rename(mapper=mapper, axis=1)
    
    return saldoxp

"""Definindo função para gerar divisão da Ágora"""
def divisao_agora(saldo_agora):
    # Lendo arquivo de saldo da Ágora
    saldoagora = pd.read_excel(saldo_agora, usecols=["CBLC", "Disponivel"])

    # Renomeando colunas
    mapper = {"CBLC": "Conta", "Disponivel": "Saldo"}
    saldoagora = saldoagora.rename(mapper=mapper, axis=1)

    # Trocando '-' por vazio na coluna 'Conta'
    saldoagora["Conta"] = saldoagora["Conta"].replace("-", "", regex=True)

    # Convertendo 'Conta' para numérico
    saldoagora["Conta"] = saldoagora["Conta"].astype(int)

    # Convertendo 'Saldo' de texto para float
    saldoagora["Saldo"] = (
        saldoagora["Saldo"]
        .astype(str)
        .str.strip()            # remove espaços no início/fim
    
    )
    saldoagora["Saldo"] = pd.to_numeric(saldoagora["Saldo"], errors="coerce")  # converte para float

    # Criando coluna 'Valor'
    saldoagora["Valor"] = np.nan

    return saldoagora


"""Definindo função para gerar uma planilha de divisão geral"""
def divisao_corretoras(divisao_btg, divisao_xp, divisao_agora, controle) :
    
    # Realizando join das planilhas por corretora com a planilha de controle
    btg = divisao_btg.merge(controle, on="Conta", how="inner")
    xp = divisao_xp.merge(controle, on="Conta", how="inner")
    agora = divisao_agora.merge(controle, on="Conta", how="inner")

    # Mudando o tipo de variável da coluna 'Saldo' do data frame da Ágora
    agora["Saldo"] = agora["Saldo"].astype(float)
    # Selecionando clientes com 'Saldo' maior ou igual a 1000 e menores que 0
    selecao_maior_1000_btg = (btg["Saldo"] >= 1000) | (btg["Saldo"] < 0)
    selecao_maior_1000_xp = (xp["Saldo"] >= 1000) | (xp["Saldo"] < 0)
    selecao_maior_1000_agora = (agora["Saldo"] >= 1000) | (agora["Saldo"] < 0)
    
    # Aplicando seleção anterior
    btg = btg[selecao_maior_1000_btg]
    xp = xp[selecao_maior_1000_xp]
    agora = agora[selecao_maior_1000_agora]
    
    
    return btg, xp, agora
