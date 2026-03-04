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
                     "Status", "Carteira", "Observações", "Situação"]
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
    
    # Garante que Valor seja numérico
    df["Valor"] = pd.to_numeric(df["Valor"], errors="coerce").fillna(0)
    
    # Função que define o operador
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
    Processa XP (mantém igual - operador vem da planilha de controle depois)
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
    Processa Ágora (mantém igual - operador vem da planilha de controle depois)
    """
    saldoagora = pd.read_excel(saldo_agora, usecols=["CBLC", "Disponivel"])

    mapper = {"CBLC": "Conta", "Disponivel": "Saldo"}
    saldoagora = saldoagora.rename(mapper=mapper, axis=1)

    saldoagora["Conta"] = saldoagora["Conta"].replace("-", "", regex=True)
    saldoagora["Conta"] = saldoagora["Conta"].astype(int)

    saldoagora["Saldo"] = (
        saldoagora["Saldo"]
        .astype(str)
        .str.strip()
    )
    saldoagora["Saldo"] = pd.to_numeric(saldoagora["Saldo"], errors="coerce")

    saldoagora["Valor"] = np.nan

    return saldoagora


def divisao_corretoras(divisao_btg, divisao_xp, divisao_agora, controle):
    """
    Junta os dados de cada corretora com a planilha de controle,
    preservando o Operador manual do BTG e usando o da planilha para XP e Ágora.
    """
    # ────────────────────────────────────────────────
    # BTG → usa Operador calculado no PL (manual)
    # ────────────────────────────────────────────────
    btg = divisao_btg.merge(
        controle,
        on="Conta",
        how="inner",
        suffixes=("_pl", "")   # evita conflito se existir "Operador" na planilha
    )

    # Prioriza o Operador que veio do PL (coluna criada em divisao_btg)
    # Se por algum motivo não existir, usa o da planilha como fallback (mas não deve acontecer)
    if "Operador_pl" in btg.columns:
        btg["Operador"] = btg["Operador_pl"]
    # Remove colunas duplicadas / temporárias
    cols_to_drop = [col for col in btg.columns if col.endswith("_pl")]
    btg = btg.drop(columns=cols_to_drop, errors="ignore")

    # ────────────────────────────────────────────────
    # XP e Ágora → usam normalmente o Operador da planilha de controle
    # ────────────────────────────────────────────────
    xp = divisao_xp.merge(controle, on="Conta", how="inner")
    agora = divisao_agora.merge(controle, on="Conta", how="inner")

    # Ajustes finais de tipo e filtro de saldo
    agora["Saldo"] = agora["Saldo"].astype(float)

    selecao_btg   = (btg["Saldo"]   >= 1000) | (btg["Saldo"]   < 0)
    selecao_xp    = (xp["Saldo"]    >= 1000) | (xp["Saldo"]    < 0)
    selecao_agora = (agora["Saldo"] >= 1000) | (agora["Saldo"] < 0)

    btg   = btg[selecao_btg].copy()
    xp    = xp[selecao_xp].copy()
    agora = agora[selecao_agora].copy()

    return btg, xp, agora
