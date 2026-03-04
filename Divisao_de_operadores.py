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
    file_path = carregar_arquivo(f"{nome_arquivo}.{tipo_arquivo.lower()}")  # Verifica se o arquivo já existe

    # Espaço de upload SEMPRE visível
    arquivo = sl.sidebar.file_uploader(
        f"📂 {nome_arquivo} ({tipo_arquivo})",
        type=[tipo_arquivo.lower()],
        help="Se já houver um arquivo salvo, ele será substituído ao enviar um novo."
    )

    # Se um novo arquivo for enviado, ele substitui o existente
    if arquivo:
        file_path = salvar_arquivo(arquivo, f"{nome_arquivo}.{tipo_arquivo.lower()}")
        sl.sidebar.success(f"✅ {nome_arquivo} salvo!")

    # Mensagem informando que o arquivo já está carregado
    if file_path:
        sl.sidebar.info(f"📄 {nome_arquivo} já carregado!")

    return file_path

# Função para aplicar cores refinadas à coluna "Status"
def highlight_status(val):
    color_map = {
        "Ativo": "#2ecc71",       # Verde suave
        "Inativo": "#f1c40f",     # Amarelo dourado
        "Encerrado": "#e74c3c",   # Vermelho elegante
        "Pode Operar": "#95a5a6"  # Cinza sofisticado
    }
    color = color_map.get(val, "white")  # Padrão: branco se não encontrado
    text_color = "black" if val == "Inativo" else "white"  # Ajusta texto para melhor visibilidade
    return f"background-color: {color}; color: {text_color}; font-weight: bold;"

# Título e descrição
sl.title("👨‍💻 Divisão de Operadores")
sl.markdown("##### 📥 **Faça o upload das planilhas em Excel na barra lateral** para dividir as contas dos clientes entre operadores.")
sl.divider()

# Upload dos arquivos em forma de dicionário
arquivos = {
    "Saldo BTG": upload_arquivo("Saldo BTG", "XLSX"),
    "PL BTG": upload_arquivo("PL BTG", "XLSX"),
    "Saldo XP": upload_arquivo("Saldo XP", "XLSX"),
    "Saldo Ágora": upload_arquivo("Saldo Ágora", "XLSX"),
    "Planilha de Controle": upload_arquivo("Planilha de Controle", "XLSX")
}

# Verifica se todos os arquivos foram enviados
if all(arquivos.values()):
    # Mensagem de sucesso caso todos os arquivos forem preenchidos
    sl.success("✅ Processamento concluído com sucesso!")
    try:
        with sl.spinner("🔄 Processando arquivos..."):
            
            # Chamando funções de processamento dos arquivos das corretoras e planilha de controle
            btg_processado = divisao_btg(arquivos["Saldo BTG"], arquivos["PL BTG"])
            xp_processado = divisao_xp(arquivos["Saldo XP"])
            agora_processado = divisao_agora(arquivos["Saldo Ágora"])
            controle_processado = coleta_controle(arquivos["Planilha de Controle"])
            
            # Chamando função para fazer as planilhas de cada corretora
            btg, xp, agora = divisao_corretoras(btg_processado, xp_processado, agora_processado, controle_processado)
            
           # Criando um layout de duas colunas: corretora e contagem de operadores
            col1, col2 = sl.columns([1.5, 1])  # Proporção para melhor equilíbrio visual

            with col1:
                sl.markdown("##### 🏦 Corretora:")
                corretora_selecionada = sl.radio("Selecione a corretora", ["BTG", "XP", "Ágora"], horizontal=True)
            
            # Definindo planilha escolhida
            df_selecionado = {"BTG": btg, "XP": xp, "Ágora": agora}[corretora_selecionada]

            # Contagem de operadores
            contagem_operador = df_selecionado["Operador"].value_counts()

            with col2:
                sl.markdown("##### 📌 Contagem de Operadores:")
                for op, c in contagem_operador.items():
                    sl.markdown(f"- **{op}**: {c} contas")
            
            sl.divider()
            
            # Criando select box para filtrar pelo operador
            operador_selecionado = sl.selectbox("Escolha o operador", options=["Gabriel", "David", "Marcus"])
            
            # Filtrando a planilha da corretora selecionada por operador e mostrando contagem por operador
            selecao_operador = df_selecionado["Operador"] == operador_selecionado
            df_filtrado = df_selecionado[selecao_operador]
            
            # Aplicando reset_index para reordenar os índices
            df_filtrado = df_filtrado.reset_index()
            
            # Ordenando por 'Saldo' e 'Carteira'
            df_filtrado = df_filtrado.sort_values(by=["Saldo", "Carteira"], ascending=False)
                
            # Mostrando planilha filtrada por operador
            sl.markdown(f"## 📊 Divisão de operação - {df_filtrado['Corretora'].unique()[0]} ({df_filtrado['Operador'].unique()[0]})")
            
            # Formatando planilha para aparecer colunas específicas
            df_filtrado = df_filtrado[["Conta", "Cliente", "Saldo", "Status", "Situação", "Carteira", "Observações", "Valor"]]

            # Substituindo None por outro valor na coluna 'Observações'
            df_filtrado["Observações"] = df_filtrado["Observações"].fillna("🏳‍🌈")
            
            # Aplicando estilo à coluna Status e formatando números
            styled_df = df_filtrado.style.map(highlight_status, subset=["Status"]).format(
                    {
                    "Valor" : lambda x : f"R$ {x:,.2f}".replace(",", "#").replace(".", ",").replace("#", "."),
                    "Saldo" : lambda x : f"R$ {x:,.2f}".replace(",", "#").replace(".", ",").replace("#", "."),
                    })
            
            # Exibir DataFrame estilizado
            sl.dataframe(styled_df)

    except Exception as e:
        sl.error(f"❌ Ocorreu um erro no processamento dos arquivos: {str(e)}")

else:
    sl.warning("⚠ Aguardando o carregamento de todos os arquivos para iniciar o processamento.")

