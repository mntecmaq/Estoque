import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO DO BANCO ---
def init_db():
    conn = sqlite3.connect('gestao_estoque.db', check_same_thread=False)
    cursor = conn.cursor()
    # 1. Tabela de Fornecedores
    cursor.execute('''CREATE TABLE IF NOT EXISTS fornecedores 
                      (id INTEGER PRIMARY KEY, nome TEXT, contato TEXT)''')
    # 2. Tabela de Produtos (com Alerta)
    cursor.execute('''CREATE TABLE IF NOT EXISTS produtos 
                      (id INTEGER PRIMARY KEY, nome TEXT, qtd INTEGER, estoque_min INTEGER)''')
    # 3. Tabela de Movimentação (Histórico)
    cursor.execute('''CREATE TABLE IF NOT EXISTS movimentacoes 
                      (id INTEGER PRIMARY KEY, data TEXT, tipo TEXT, 
                       produto_id INTEGER, qtd INTEGER, destino_origem TEXT)''')
    conn.commit()
    return conn

conn = init_db()

# --- INTERFACE STREAMLIT ---
st.title("🛠️ Sistema de Gestão de Estoque")

menu = ["Estoque Atual", "Cadastrar Fornecedor", "Entrada (Compra)", "Saída (Uso/Venda)"]
choice = st.sidebar.selectbox("Menu", menu)

# --- 1. ESTOQUE ATUAL & ALERTAS ---
if choice == "Estoque Atual":
    st.subheader("📋 Status do Inventário")
    df = pd.read_sql_query("SELECT * FROM produtos", conn)
    
    # Alerta de Estoque Zerado ou Baixo
    for index, row in df.iterrows():
        if row['qtd'] <= 0:
            st.error(f"🚨 PRODUTO ZERADO: {row['nome']}")
        elif row['qtd'] <= row['estoque_min']:
            st.warning(f"⚠️ Estoque Baixo: {row['nome']} (Apenas {row['qtd']} un)")
    
    st.table(df)

# --- 2. CADASTRO DE FORNECEDOR ---
elif choice == "Cadastrar Fornecedor":
    st.subheader("🚚 Novo Fornecedor")
    nome_f = st.text_input("Nome da Empresa/Vendedor")
    contato = st.text_input("Telefone ou E-mail")
    if st.button("Salvar Fornecedor"):
        conn.execute("INSERT INTO fornecedores (nome, contato) VALUES (?,?)", (nome_f, contato))
        conn.commit()
        st.success("Fornecedor cadastrado!")

# --- 3. ENTRADA DE MATERIAL ---
elif choice == "Entrada (Compra)":
    st.subheader("📥 Registrar Compra")
    fornecedores = pd.read_sql_query("SELECT id, nome FROM fornecedores", conn)
    forn_choice = st.selectbox("Selecione o Fornecedor", fornecedores['nome'].tolist())
    
    produto_nome = st.text_input("Nome do Produto")
    qtd_entrada = st.number_input("Quantidade Comprada", min_value=1)
    est_min = st.number_input("Alerta de estoque mínimo (un)", min_value=1)
    
    if st.button("Confirmar Entrada"):
        # Verifica se produto já existe
        res = conn.execute("SELECT id, qtd FROM produtos WHERE nome = ?", (produto_nome,)).fetchone()
        if res:
            nova_qtd = res[1] + qtd_entrada
            conn.execute("UPDATE produtos SET qtd = ? WHERE id = ?", (nova_qtd, res[0]))
        else:
            conn.execute("INSERT INTO produtos (nome, qtd, estoque_min) VALUES (?,?,?)", 
                         (produto_nome, qtd_entrada, est_min))
        
        conn.execute("INSERT INTO movimentacoes (data, tipo, produto_id, qtd, destino_origem) VALUES (?,?,?,?,?)",
                     (datetime.now().strftime("%d/%m/%Y %H:%M"), "ENTRADA", produto_nome, qtd_entrada, forn_choice))
        conn.commit()
        st.success("Estoque atualizado!")

# --- 4. SAÍDA DE MATERIAL ---
elif choice == "Saída (Uso/Venda)":
    st.subheader("📤 Registrar Uso ou Venda")
    produtos = pd.read_sql_query("SELECT nome FROM produtos WHERE qtd > 0", conn)
    prod_choice = st.selectbox("Produto a retirar", produtos['nome'].tolist())
    qtd_saida = st.number_input("Quantidade", min_value=1)
    destino = st.text_input("Destino (Ex: Cliente João / Técnico Silva / OS 452)")
    
    if st.button("Confirmar Saída"):
        res = conn.execute("SELECT id, qtd FROM produtos WHERE nome = ?", (prod_choice,)).fetchone()
        if res[1] >= qtd_saida:
            nova_qtd = res[1] - qtd_saida
            conn.execute("UPDATE produtos SET qtd = ? WHERE id = ?", (nova_qtd, res[0]))
            conn.execute("INSERT INTO movimentacoes (data, tipo, produto_id, qtd, destino_origem) VALUES (?,?,?,?,?)",
                         (datetime.now().strftime("%d/%m/%Y %H:%M"), "SAÍDA", prod_choice, qtd_saida, destino))
            conn.commit()
            st.success(f"Saída de {prod_choice} registrada para {destino}!")
        else:
            st.error("Quantidade insuficiente no estoque!")
