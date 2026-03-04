# -*- coding: utf-8 -*-
"""
Backend blindado - Divisão de Operadores
"""

# =========================
# IMPORTAÇÕES
# =========================
import pandas as pd
import numpy as np


# =========================
# FUNÇÃO AUXILIAR GLOBAL
# =========================
def padronizar_conta(df):
    """
    Padroniza coluna Conta para evitar erro de merge
    """
    df["Conta"] = (
        df["Conta"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )
    return df


def padronizar_saldo(df):
    """
    Garante que coluna Saldo seja numérica
    """
    df["Saldo"] = (
        df["Saldo"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    df["Saldo"] = pd.to_numeric(df["Saldo"], errors="coerce")

    return df


# =========================
# COLETA CONTROLE
# =========================
def coleta_controle(controle):

    planilha_controle = pd.ExcelFile(controle)
    corretoras = ["BTG", "XP", "Ágora"]
    dataframes = []

    for c in corretoras:
        planilha = planilha_controle.parse(
            c,
            skiprows=1,
            skipfooter=5,
            usecols=[
                "Conta",
                "Cliente",
                "Corretora",
                "Operador",
                "Status",
                "Carteira",
                "Observações",
                "Situação",
            ],
        )

        planilha = padronizar_conta(planilha)
        dataframes.append(planilha)

    df_agregado = pd.concat(dataframes, ignore_index=True)

    return df_agregado


# =========================
# DIVISÃO BTG
# =========================
def divisao_btg(saldo_btg, pl_btg):

    saldobtg = pd.read_excel(
        saldo_btg,
        usecols=["Conta", "Saldo"],
        skipfooter=2,
    )

    plbtg = pd.read_excel(
        pl_btg,
        usecols=["Conta", "Valor"],
        skipfooter=2,
    )

    saldobtg = padronizar_conta(saldobtg)
    plbtg = padronizar_conta(plbtg)

    saldobtg = padronizar_saldo(saldobtg)

    df_saldo_btg = saldobtg.merge(
        plbtg,
        on="Conta",
        how="outer",
    )

    return df_saldo_btg


# =========================
# DIVISÃO XP
# =========================
def divisao_xp(saldo_xp):

    saldoxp = pd.read_excel(
        saldo_xp,
        usecols=["COD. CLIENTE", "PATRIMÔNIO TOTAL", "SALDO TOTAL"],
    )

    mapper = {
        "COD. CLIENTE": "Conta",
        "PATRIMÔNIO TOTAL": "Valor",
        "SALDO TOTAL": "Saldo",
    }

    saldoxp = saldoxp.rename(mapper=mapper, axis=1)

    saldoxp = padronizar_conta(saldoxp)
    saldoxp = padronizar_saldo(saldoxp)

    return saldoxp


# =========================
# DIVISÃO ÁGORA
# =========================
def divisao_agora(saldo_agora):

    saldoagora = pd.read_excel(
        saldo_agora,
        usecols=["CBLC", "Disponível"],
    )

    mapper = {
        "CBLC": "Conta",
        "Disponível": "Saldo",
    }

    saldoagora = saldoagora.rename(mapper=mapper, axis=1)

    saldoagora["Conta"] = saldoagora["Conta"].replace("-", "")

    saldoagora = padronizar_conta(saldoagora)
    saldoagora = padronizar_saldo(saldoagora)

    saldoagora["Valor"] = np.nan

    return saldoagora


# =========================
# DIVISÃO FINAL
# =========================
def divisao_corretoras(divisao_btg, divisao_xp, divisao_agora, controle):

    # Garantindo padronização geral
    for df in [divisao_btg, divisao_xp, divisao_agora, controle]:
        df["Conta"] = (
            df["Conta"]
            .astype(str)
            .str.replace(".0", "", regex=False)
            .str.strip()
        )

    # Merge
    btg = divisao_btg.merge(controle, on="Conta", how="inner")
    xp = divisao_xp.merge(controle, on="Conta", how="inner")
    agora = divisao_agora.merge(controle, on="Conta", how="inner")

    # Garantindo saldo numérico
    for df in [btg, xp, agora]:
        df["Saldo"] = pd.to_numeric(df["Saldo"], errors="coerce")

    # Filtro >= 1000 ou negativo
    btg = btg[(btg["Saldo"] >= 1000) | (btg["Saldo"] < 0)]
    xp = xp[(xp["Saldo"] >= 1000) | (xp["Saldo"] < 0)]
    agora = agora[(agora["Saldo"] >= 1000) | (agora["Saldo"] < 0)]

    return btg, xp, agora
