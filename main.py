import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO SUPABASE ---
# Substitua pelos dados que copiou do seu painel Supabase
SUPABASE_URL = "https://idbhzlgzaqbmaultxlwc.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImlkYmh6bGd6YXFibWF1bHR4bHdjIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM2MTU1MTUsImV4cCI6MjA4OTE5MTUxNX0.JSECB48WC_z-tY4U3kD7yluTFBqerxf0pStDGOVuWbA"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Gestão de estoque Profissional", layout="wide")
st.title("🛠️ Sistema de Gestão de estoque (Nuvem)")

menu = ["estoque Atual", "Cadastrar Fornecedor", "Entrada (Compra)", "Saída (Uso/Venda)"]
choice = st.sidebar.selectbox("Menu de Navegação", menu)

# --- 1. STOCK ATUAL & ALERTAS ---
if choice == "Stock Atual":
    st.subheader("📋 Status do Inventário em Tempo Real")
    
    # Busca dados da tabela 'produtos' no Supabase
    response = supabase.table("produtos").select("*").execute()
    if response.data:
        df = pd.DataFrame(response.data)
        
        # Lógica de Alertas
        for _, row in df.iterrows():
            if row['qtd'] <= 0:
                st.error(f"🚨 PRODUTO ZERADO: {row['nome']}")
            elif row['qtd'] <= row['estoque_min']:
                st.warning(f"⚠️ estoque Baixo: {row['nome']} (Apenas {row['qtd']} un)")
        
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Nenhum produto cadastrado ainda.")

# --- 2. CADASTRO DE FORNECEDOR ---
elif choice == "Cadastrar Fornecedor":
    st.subheader("🚚 Novo Fornecedor")
    
    # Criamos um formulário para encapsular os campos
    with st.form("form_fornecedor", clear_on_submit=True):
        nome_f = st.text_input("Nome da Empresa/Vendedor")
        contato = st.text_input("Telefone ou E-mail")
        
        # O botão agora é a única porta de entrada para o banco
        submit_button = st.form_submit_button("Salvar Fornecedor")
        
        # A lógica só roda se o botão for pressionado
        if submit_button:
            if nome_f: # Verifica se o nome não está vazio
                supabase.table("fornecedores").insert({"nome": nome_f, "contato": contato}).execute()
                st.success(f"Fornecedor {nome_f} cadastrado com sucesso!")
            else:
                st.warning("O nome do fornecedor é obrigatório.")

# --- 3. ENTRADA DE MATERIAL ---
elif choice == "Entrada (Compra)":
    st.subheader("📥 Registrar Compra")
    
    # Carregar fornecedores para o selectbox
    forn_data = supabase.table("fornecedores").select("nome").execute()
    lista_forn = [f['nome'] for f in forn_data.data] if forn_data.data else []
    
    with st.form("form_entrada"):
        forn_choice = st.selectbox("Selecione o Fornecedor", lista_forn)
        produto_nome = st.text_input("Nome do Produto")
        qtd_entrada = st.number_input("Quantidade Comprada", min_value=1)
        est_min = st.number_input("Alerta de estoque mínimo (un)", min_value=1)
        
        if st.form_submit_button("Confirmar Entrada"):
            # Verifica se produto já existe
            res = supabase.table("produtos").select("*").eq("nome", produto_nome).execute()
            
            if res.data:
                nova_qtd = res.data[0]['qtd'] + qtd_entrada
                supabase.table("produtos").update({"qtd": nova_qtd}).eq("nome", produto_nome).execute()
            else:
                supabase.table("produtos").insert({"nome": produto_nome, "qtd": qtd_entrada, "estoque_min": est_min}).execute()
            
            # Regista histórico
            supabase.table("movimentacoes").insert({
                "data": datetime.now().isoformat(),
                "tipo": "ENTRADA",
                "produto": produto_nome,
                "qtd": qtd_entrada,
                "origem_destino": forn_choice
            }).execute()
            st.success("estoque atualizado com sucesso!")

# --- 4. SAÍDA DE MATERIAL ---
elif choice == "Saída (Uso/Venda)":
    st.subheader("📤 Registrar Uso ou Venda")
    
    prod_data = supabase.table("produtos").select("nome").gt("qtd", 0).execute()
    lista_prod = [p['nome'] for p in prod_data.data] if prod_data.data else []
    
    with st.form("form_saida"):
        prod_choice = st.selectbox("Produto a retirar", lista_prod)
        qtd_saida = st.number_input("Quantidade", min_value=1)
        destino = st.text_input("Destino (Ex: Cliente João / OS 452)")
        
        if st.form_submit_button("Confirmar Saída"):
            res = supabase.table("produtos").select("id", "qtd").eq("nome", prod_choice).execute()
            if res.data and res.data[0]['qtd'] >= qtd_saida:
                nova_qtd = res.data[0]['qtd'] - qtd_saida
                supabase.table("produtos").update({"qtd": nova_qtd}).eq("id", res.data[0]['id']).execute()
                
                supabase.table("movimentacoes").insert({
                    "data": datetime.now().isoformat(),
                    "tipo": "SAÍDA",
                    "produto": prod_choice,
                    "qtd": qtd_saida,
                    "origem_destino": destino
                }).execute()
                st.success(f"Saída registada!")
            else:
                st.error("Quantidade insuficiente!")
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
