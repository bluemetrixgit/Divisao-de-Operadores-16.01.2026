# -*- coding: utf-8 -*-
"""
Created on Sat Mar  1 17:41:44 2025
@author: Marqu
"""

# =========================
# IMPORTAÇÕES
# =========================
import streamlit as sl
import os
import warnings

from backend import (
    coleta_controle,
    divisao_btg,
    divisao_xp,
    divisao_agora,
    divisao_corretoras
)

# =========================
# CONFIGURAÇÕES GERAIS
# =========================
warnings.filterwarnings(
    "ignore",
    message="Workbook contains no default style*"
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

sl.set_page_config(
    page_title="Divisão de Operadores",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

sl.write("🟢 App iniciado")

# =========================
# FUNÇÕES AUXILIARES
# =========================
def salvar_arquivo(uploaded_file, filename):
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path


def carregar_arquivo(filename):
    file_path = os.path.join(UPLOAD_DIR, filename)
    return file_path if os.path.exists(file_path) else None


def upload_arquivo(nome_arquivo, tipo_arquivo):
    file_path = carregar_arquivo(f"{nome_arquivo}.{tipo_arquivo.lower()}")

    arquivo = sl.sidebar.file_uploader(
        f"📂 {nome_arquivo} ({tipo_arquivo})",
        type=[tipo_arquivo.lower()],
        help="Se já houver um arquivo salvo, ele será substituído."
    )

    if arquivo:
        file_path = salvar_arquivo(arquivo, f"{nome_arquivo}.{tipo_arquivo.lower()}")
        sl.sidebar.success(f"✅ {nome_arquivo} salvo!")

    if file_path:
        sl.sidebar.info(f"📄 {nome_arquivo} carregado")

    return file_path


def highlight_status(val):
    color_map = {
        "Ativo": "#2ecc71",
        "Inativo": "#f1c40f",
        "Encerrado": "#e74c3c",
        "Pode Operar": "#95a5a6",
    }
    color = color_map.get(val, "white")
    text_color = "black" if val == "Inativo" else "white"
    return f"background-color: {color}; color: {text_color}; font-weight: bold;"


# =========================
# INTERFACE
# =========================
sl.title("👨‍💻 Divisão de Operadores")
sl.markdown(
    "##### 📥 **Faça o upload das planilhas em Excel na barra lateral** "
    "para dividir as contas dos clientes entre operadores."
)
sl.divider()

arquivos = {
    "Saldo BTG": upload_arquivo("Saldo BTG", "XLSX"),
    "PL BTG": upload_arquivo("PL BTG", "XLSX"),
    "Saldo XP": upload_arquivo("Saldo XP", "XLSX"),
    "Saldo Ágora": upload_arquivo("Saldo Ágora", "XLSX"),
    "Planilha de Controle": upload_arquivo("Planilha de Controle", "XLSX"),
}

# =========================
# PROCESSAMENTO
# =========================
if all(arquivos.values()):
    sl.success("✅ Todos os arquivos carregados")
    sl.write("📂 Iniciando processamento")

    try:
        with sl.spinner("🔄 Processando arquivos..."):

            sl.write("⚙ Processando BTG")
            try:
                btg_processado = divisao_btg(
                    arquivos["Saldo BTG"], arquivos["PL BTG"]
                )
            except Exception as e:
                sl.error("❌ Erro no processamento do BTG")
                sl.exception(e)
                sl.stop()

            sl.write("⚙ Processando XP")
            try:
                xp_processado = divisao_xp(arquivos["Saldo XP"])
            except Exception as e:
                sl.error("❌ Erro no processamento da XP")
                sl.exception(e)
                sl.stop()

            sl.write("⚙ Processando Ágora")
            try:
                agora_processado = divisao_agora(arquivos["Saldo Ágora"])
            except Exception as e:
                sl.error("❌ Erro no processamento da Ágora")
                sl.exception(e)
                sl.stop()

            sl.write("⚙ Processando Planilha de Controle")
            try:
                controle_processado = coleta_controle(
                    arquivos["Planilha de Controle"]
                )
            except Exception as e:
                sl.error("❌ Erro na planilha de controle")
                sl.exception(e)
                sl.stop()

            btg, xp, agora = divisao_corretoras(
                btg_processado,
                xp_processado,
                agora_processado,
                controle_processado
            )

        # =========================
        # SELEÇÃO DE CORRETORA
        # =========================
        col1, col2 = sl.columns([1.5, 1])

        with col1:
            corretora_selecionada = sl.radio(
                "🏦 Selecione a corretora",
                ["BTG", "XP", "Ágora"],
                horizontal=True
            )

        df_selecionado = {
            "BTG": btg,
            "XP": xp,
            "Ágora": agora
        }[corretora_selecionada]

        contagem_operador = df_selecionado["Operador"].value_counts()

        with col2:
            sl.markdown("##### 📌 Contagem de Operadores:")
            for op, c in contagem_operador.items():
                sl.markdown(f"- **{op}**: {c} contas")

        sl.divider()

        operador_selecionado = sl.selectbox(
            "Escolha o operador",
            sorted(df_selecionado["Operador"].unique())
        )

        df_filtrado = df_selecionado[
            df_selecionado["Operador"] == operador_selecionado
        ].reset_index(drop=True)

        if df_filtrado.empty:
            sl.warning("⚠ Nenhum registro encontrado para o operador selecionado.")
            sl.stop()

        df_filtrado = df_filtrado.sort_values(
            by=["Saldo", "Carteira"],
            ascending=False
        )

        sl.markdown(
            f"## 📊 Divisão de operação - "
            f"{df_filtrado['Corretora'].iloc[0]} "
            f"({df_filtrado['Operador'].iloc[0]})"
        )

        df_filtrado = df_filtrado[
            ["Conta", "Cliente", "Saldo", "Status", "Situação",
             "Carteira", "Observações", "Valor"]
        ]

        df_filtrado["Observações"] = df_filtrado["Observações"].fillna("🏳‍🌈")

        if df_filtrado.shape[0] > 5000:
            sl.warning(
                "⚠ Muitos registros para exibição com estilo. "
                "Mostrando tabela simples."
            )
            sl.dataframe(df_filtrado)
            sl.stop()

        styled_df = (
            df_filtrado
            .style
            .map(highlight_status, subset=["Status"])
            .format({
                "Valor": lambda x: f"R$ {x:,.2f}"
                .replace(",", "#").replace(".", ",").replace("#", "."),
                "Saldo": lambda x: f"R$ {x:,.2f}"
                .replace(",", "#").replace(".", ",").replace("#", "."),
            })
        )

        sl.dataframe(styled_df)

    except Exception as e:
        sl.error("❌ Erro inesperado no aplicativo")
        sl.exception(e)

else:
    sl.warning("⚠ Aguardando o carregamento de todos os arquivos.")
