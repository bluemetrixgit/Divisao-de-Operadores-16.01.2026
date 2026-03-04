# -*- coding: utf-8 -*-
"""
Created on Fri Feb 28 17:56:31 2025

@author: Marco Marques de Castro
"""

import pandas as pd
import numpy as np

def coleta_controle(controle):
    """
    Lê a planilha de controle e agrega as abas BTG, XP e Ágora
    """
    planilha_controle = pd.ExcelFile(controle)
    corretoras = ["BTG", "XP", "Ágora"]
    dataframes = []
    
    for c in corretoras:
        planilha = planilha_controle.parse(
            c,
            skiprows=1,
            skipfooter=5,
            usecols=["Conta", "Cliente", "Corretora", "Operador",
                     "Status", "Carteira", "Observações", "Situação", "BP"]  # Adicionada "BP" para Ágora
        )
        dataframes.append(planilha)
    
    df_agregado = pd.concat(dataframes, ignore_index=True)
    return df_agregado


def divisao_btg(saldo_btg, pl_btg):
    """
    Processa BTG e define operador MANUALMENTE com base no PL:
      PL < 250.000     → David
      250.000 ≤ PL ≤ 800.000 → Gabriel
      PL > 800.000     → Marcus
    """
    saldobtg = pd.read_excel(saldo_btg, usecols=["Conta", "Saldo"], skipfooter=2)
    plbtg    = pd.read_excel(pl_btg,    usecols=["Conta", "Valor"], skipfooter=2)
    
    df = saldobtg.merge(plbtg, on="Conta", how="outer")
    
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    
    def atribuir_operador(pl):
        if pl < 250_000:
            return "David"
        elif pl <= 800_000:
            return "Gabriel"
        else:
            return "Marcus"
    
    df["Operador"] = df["Valor"].apply(atribuir_operador)
    
    return df


def divisao_xp(saldo_xp):
    """
    Processa XP (operador vem da planilha de controle depois)
    """
    saldoxp = pd.read_excel(saldo_xp, usecols=["COD. CLIENTE", "PATRIMÔNIO TOTAL", "D0"])
    
    mapper = {
        "COD. CLIENTE": "Conta",
        "PATRIMÔNIO TOTAL": "Valor",
        "D0": "Saldo"
    }
    saldoxp = saldoxp.rename(mapper=mapper, axis=1)
    
    return saldoxp


def divisao_agora(saldo_agora):
    """
    Processa saldo da Ágora (PL será trazido depois via merge com "BP")
    """
    saldoagora = pd.read_excel(saldo_agora, usecols=["CBLC", "Disponivel"])

    mapper = {"CBLC": "Conta", "Disponivel": "Saldo"}
    saldoagora = saldoagora.rename(mapper=mapper, axis=1)

    saldoagora["Conta"] = saldoagora["Conta"].replace("-", "", regex=True)
    saldoagora["Conta"] = pd.to_numeric(saldoagora["Conta"], errors="coerce").astype("Int64")  # mais seguro

    saldoagora["Saldo"] = (
        saldoagora["Saldo"]
        .astype(str)
        .str.strip()
        .str.replace(".", "", regex=False)   # remove separador de milhar se houver
        .str.replace(",", ".", regex=False)
    )
    saldoagora["Saldo"] = pd.to_numeric(saldoagora["Saldo"], errors="coerce")

    # NÃO criamos Valor aqui → será trazido do merge com "BP" da planilha de controle
    return saldoagora


def divisao_corretoras(divisao_btg, divisao_xp, divisao_agora, controle):
    """
    Junta os dados e trata PL/Valor de forma específica por corretora:
    - BTG: Valor do arquivo PL BTG + Operador manual
    - XP:  Valor do arquivo Saldo XP
    - Ágora: Valor = coluna "BP" da aba Ágora da planilha de controle
    """
    # ────────────────────────────────────────────────
    # BTG → Operador manual (do PL), Valor já existe
    # ────────────────────────────────────────────────
    btg = divisao_btg.merge(
        controle,
        on="Conta",
        how="inner",
        suffixes=("_pl", "")
    )
    # Prioriza Operador manual
    if "Operador_pl" in btg.columns:
        btg["Operador"] = btg["Operador_pl"]
    # Limpa colunas temporárias
    cols_to_drop = [col for col in btg.columns if col.endswith("_pl")]
    btg = btg.drop(columns=cols_to_drop, errors="ignore")

    # ────────────────────────────────────────────────
    # XP → normal
    # ────────────────────────────────────────────────
    xp = divisao_xp.merge(controle, on="Conta", how="inner")

    # ────────────────────────────────────────────────
    # Ágora → traz PL da coluna "BP" e renomeia para "Valor"
    # ────────────────────────────────────────────────
    agora = divisao_agora.merge(controle, on="Conta", how="inner")
    # Renomeia BP → Valor (consistência com outras corretoras)
    if "BP" in agora.columns:
        agora["Valor"] = pd.to_numeric(agora["BP"], errors="coerce")
        agora = agora.drop(columns=["BP"], errors="ignore")  # remove original se quiser

    # Ajustes finais de tipo e filtro
    agora["Saldo"] = agora["Saldo"].astype(float)

    selecao_btg   = (btg["Saldo"]   >= 1000) | (btg["Saldo"]   < 0)
    selecao_xp    = (xp["Saldo"]    >= 1000) | (xp["Saldo"]    < 0)
    selecao_agora = (agora["Saldo"] >= 1000) | (agora["Saldo"] < 0)

    btg   = btg[selecao_btg].copy()
    xp    = xp[selecao_xp].copy()
    agora = agora[selecao_agora].copy()

    return btg, xp, agora
