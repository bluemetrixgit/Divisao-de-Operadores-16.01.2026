# -*- coding: utf-8 -*-

import pandas as pd
import numpy as np


# =========================
# CONTROLE
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
                "Conta", "Cliente", "Corretora", "Operador",
                "Status", "Carteira", "Observações", "Situação"
            ]
        )

        # Padroniza Conta
        planilha["Conta"] = (
            planilha["Conta"]
            .astype(str)
            .str.replace(".0", "", regex=False)
            .str.strip()
        )

        dataframes.append(planilha)

    df_agregado = pd.concat(dataframes, ignore_index=True)

    return df_agregado


# =========================
# BTG
# =========================
def divisao_btg(saldo_btg, pl_btg):

    saldobtg = pd.read_excel(
        saldo_btg,
        usecols=["Conta", "Saldo"],
        skipfooter=2
    )

    plbtg = pd.read_excel(
        pl_btg,
        usecols=["Conta", "Valor"],
        skipfooter=2
    )

    # Padroniza Conta nos dois dataframes
    for df in [saldobtg, plbtg]:
        df["Conta"] = (
            df["Conta"]
            .astype(str)
            .str.replace(".0", "", regex=False)
            .str.strip()
        )

    # 🔥 Converte saldo corretamente (essa é a parte crítica)
    saldobtg["Saldo"] = (
        saldobtg["Saldo"]
        .astype(str)
        .str.replace(".", "", regex=False)
        .str.replace(",", ".", regex=False)
        .str.strip()
    )

    saldobtg["Saldo"] = pd.to_numeric(saldobtg["Saldo"], errors="coerce")

    df_saldo_btg = saldobtg.merge(plbtg, on="Conta", how="outer")

    return df_saldo_btg


# =========================
# XP
# =========================
def divisao_xp(saldo_xp):

    saldoxp = pd.read_excel(
        saldo_xp,
        usecols=["COD. CLIENTE", "PATRIMÔNIO TOTAL", "D0"]
    )

    mapper = {
        "COD. CLIENTE": "Conta",
        "PATRIMÔNIO TOTAL": "Valor",
        "D0": "Saldo"
    }

    saldoxp = saldoxp.rename(columns=mapper)

    saldoxp["Conta"] = (
        saldoxp["Conta"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.strip()
    )

    saldoxp["Saldo"] = pd.to_numeric(saldoxp["Saldo"], errors="coerce")

    return saldoxp


# =========================
# ÁGORA
# =========================
def divisao_agora(saldo_agora):

    saldoagora = pd.read_excel(
        saldo_agora,
        usecols=["CBLC", "Disponivel"]
    )

    saldoagora = saldoagora.rename(
        columns={"CBLC": "Conta", "Disponivel": "Saldo"}
    )

    saldoagora["Conta"] = (
        saldoagora["Conta"]
        .astype(str)
        .str.replace("-", "")
        .str.strip()
    )

    saldoagora["Saldo"] = pd.to_numeric(
        saldoagora["Saldo"],
        errors="coerce"
    )

    saldoagora["Valor"] = np.nan

    return saldoagora


# =========================
# DIVISÃO FINAL
# =========================
def normalizar_conta_forte(df):
    df["Conta"] = (
        df["Conta"]
        .astype(str)
        .str.replace(".0", "", regex=False)
        .str.replace("-", "", regex=False)
        .str.replace(" ", "", regex=False)
        .str.strip()
        .str.zfill(8)   # 🔥 força tamanho padrão (ajuste se necessário)
    )
    return df


def divisao_corretoras(divisao_btg, divisao_xp, divisao_agora, controle):

    # 🔥 NORMALIZAÇÃO FORTE
    divisao_btg = normalizar_conta_forte(divisao_btg)
    divisao_xp = normalizar_conta_forte(divisao_xp)
    divisao_agora = normalizar_conta_forte(divisao_agora)
    controle = normalizar_conta_forte(controle)

    # 🔥 MERGE CONTROLADO COM INDICADOR
    btg = divisao_btg.merge(
        controle,
        on="Conta",
        how="left",
        indicator=True
    )

    # Debug temporário (pode remover depois)
    print("BTG merge status:")
    print(btg["_merge"].value_counts())

    btg = btg.drop(columns=["_merge"])

    xp = divisao_xp.merge(controle, on="Conta", how="left")
    agora = divisao_agora.merge(controle, on="Conta", how="left")

    # Saldo numérico
    for df in [btg, xp, agora]:
        df["Saldo"] = pd.to_numeric(df["Saldo"], errors="coerce")

    # Filtro >= 1000 ou negativo
    btg = btg[(btg["Saldo"] >= 1000) | (btg["Saldo"] < 0)]
    xp = xp[(xp["Saldo"] >= 1000) | (xp["Saldo"] < 0)]
    agora = agora[(agora["Saldo"] >= 1000) | (agora["Saldo"] < 0)]

    return btg, xp, agora
