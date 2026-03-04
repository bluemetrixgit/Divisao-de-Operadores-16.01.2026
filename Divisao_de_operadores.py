# -*- coding: utf-8 -*-
"""
Created on Sat Mar  1 17:41:44 2025

@author: Marqu
"""

# Importação de bibliotecas
import streamlit as sl
import os
from backend import coleta_controle, divisao_btg, divisao_xp, divisao_agora, divisao_corretoras

# Diretório para salvar os arquivos
UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)  # Cria a pasta caso não exista

# Configuração da página
sl.set_page_config(
    page_title="Divisão de Operadores",
    page_icon="👨‍💻",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Função para salvar arquivo de forma global
def salvar_arquivo(uploaded_file, filename):
    """Salva o arquivo no diretório compartilhado para todos os usuários"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Função para verificar se um arquivo salvo já existe
def carregar_arquivo(filename):
    """Retorna o caminho do arquivo salvo globalmente, se existir"""
    file_path = os.path.join(UPLOAD_DIR, filename)
    return file_path if os.path.exists(file_path) else None

# Função de upload que mantém os arquivos carregados visíveis e permite substituição
def upload_arquivo(nome_arquivo, tipo_arquivo):
    """Mantém o espaço de upload sempre visível e permite substituir arquivos"""
    file_path = carregar_arquivo(f"{nome_arquivo}.{tipo_arquivo.lower()}")

    arquivo = sl.sidebar.file_uploader(
        f"📂 {nome_arquivo} ({tipo_arquivo})",
        type=[tipo_arquivo.lower()],
        help="Se já houver um arquivo salvo, ele será substituído ao enviar um novo."
    )

    if arquivo:
        file_path = salvar_arquivo(arquivo, f"{nome_arquivo}.{tipo_arquivo.lower()}")
        sl.sidebar.success(f"✅ {nome_arquivo} salvo!")

    if file_path:
        sl.sidebar.info(f"📄 {nome_arquivo} já carregado!")

    return file_path

# Função para aplicar cores refinadas à coluna "Status"
def highlight_status(val):
    color_map = {
        "Ativo": "#2ecc71",
        "Inativo": "#f1c40f",
        "Encerrado": "#e74c3c",
        "Pode Operar": "#95a5a6"
    }
    color = color_map.get(val, "white")
    text_color = "black" if val == "Inativo" else "white"
    return f"background-color: {color}; color: {text_color}; font-weight: bold;"

# Título e descrição
sl.title("👨‍💻 Divisão de Operadores")
sl.markdown("##### 📥 **Faça o upload das planilhas em Excel na barra lateral** para dividir as contas dos clientes entre operadores.")
sl.divider()

# Upload dos arquivos
arquivos = {
    "Saldo BTG": upload_arquivo("Saldo BTG", "XLSX"),
    "PL BTG": upload_arquivo("PL BTG", "XLSX"),
    "Saldo XP": upload_arquivo("Saldo XP", "XLSX"),
    "Saldo Ágora": upload_arquivo("Saldo Ágora", "XLSX"),
    "Planilha de Controle": upload_arquivo("Planilha de Controle", "XLSX")
}

if all(arquivos.values()):
    sl.success("✅ Processamento concluído com sucesso!")
    try:
        with sl.spinner("🔄 Processando arquivos..."):

            btg_processado = divisao_btg(arquivos["Saldo BTG"], arquivos["PL BTG"])
            xp_processado = divisao_xp(arquivos["Saldo XP"])
            agora_processado = divisao_agora(arquivos["Saldo Ágora"])
            controle_processado = coleta_controle(arquivos["Planilha de Controle"])

            btg, xp, agora = divisao_corretoras(
                btg_processado,
                xp_processado,
                agora_processado,
                controle_processado
            )

            col1, col2 = sl.columns([1.5, 1])

            with col1:
                sl.markdown("##### 🏦 Corretora:")
                corretora_selecionada = sl.radio(
                    "Selecione a corretora",
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
                options=["Gabriel", "David", "Marcus"]
            )

            df_filtrado = df_selecionado[
                df_selecionado["Operador"] == operador_selecionado
            ].reset_index()

            df_filtrado = df_filtrado.sort_values(
                by=["Saldo", "Carteira"],
                ascending=False
            )

            sl.markdown(
                f"## 📊 Divisão de operação - "
                f"{df_filtrado['Corretora'].unique()[0]} "
                f"({df_filtrado['Operador'].unique()[0]})"
            )

            df_filtrado = df_filtrado[
                ["Conta", "Cliente", "Saldo", "Status",
                 "Situação", "Carteira", "Observações", "Valor"]
            ]

            df_filtrado["Observações"] = df_filtrado["Observações"].fillna("🏳‍🌈")

            styled_df = df_filtrado.style.map(
                highlight_status,
                subset=["Status"]
            ).format(
                {
                    "Valor": lambda x: f"R$ {x:,.2f}".replace(",", "#").replace(".", ",").replace("#", "."),
                    "Saldo": lambda x: f"R$ {x:,.2f}".replace(",", "#").replace(".", ",").replace("#", "."),
                }
            )

            # 🔥 MODIFICAÇÃO AQUI
            sl.write(styled_df)

    except Exception as e:
        sl.error(f"❌ Ocorreu um erro no processamento dos arquivos: {str(e)}")

else:
    sl.warning("⚠ Aguardando o carregamento de todos os arquivos para iniciar o processamento.")
