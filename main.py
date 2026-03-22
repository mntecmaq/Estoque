import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime

# --- CONFIGURAÇÃO SUPABASE ---
# Substitua pelos dados que copiou do seu painel Supabase
SUPABASE_URL = "https://wtcpvrzwrniklnmmywbb.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Ind0Y3B2cnp3cm5pa2xubW15d2JiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzM3OTMzNDMsImV4cCI6MjA4OTM2OTM0M30.gFzLiHlec9ClsmvhxBkkPktQDJ04w2e-KdlWidb0qlc"

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# --- INTERFACE STREAMLIT ---
st.set_page_config(page_title="Gestão de estoque Profissional", layout="wide")
st.title("🛠️ Sistema de Gestão de estoque (Nuvem)")

#menu = ["Cadastro de Cliente", "Estoque Atual", "Cadastrar Fornecedor", "Entrada (Compra)", "Saída (Uso/Venda)"]
#choice = st.sidebar.selectbox("Menu de Navegação", menu)
# Adicione após a linha 18:
menu = ["Cadastro de Cliente", "Estoque Atual", "Cadastrar Fornecedor", "Entrada (Compra)", "Saída (Uso/Venda)"]
choice = st.sidebar.selectbox("Menu de Navegação", menu)

# Fechar/esconder o sidebar após seleção
if choice:
    st.sidebar.write("")  # Placeholder para fechar visualmente

# --- 1. REGISTRO DE CLIENTES ---
if choice == "Cadastro de Cliente":
    st.subheader("Novo Cliente")

    # Criamos um formulário para encapsular os campos
    with st.form("form_cliente", clear_on_submit=True):
        nome_cli = st.text_input("Nome do cliente")
        fone_cli = st.text_input("Telefone ou E-mail")
        local_cli = st.text_input("Endereço")

        # O botão agora é a única porta de entrada para o banco
        submit_button = st.form_submit_button("Salvar Cliente")

        # A lógica só roda se o botão for pressionado
        if submit_button:
		
			if nome_cli and fone_cli.isdigit():
				supabase.table("cliente").insert({"nome_cli": nome_cli, "fone_cli": fone_cli, "local_cli": local_cli}).execute()
					st.success(f"Cliente {nome_cli} cadastrado com sucesso!")

					elif not nome_cli:
					st.warning("O nome do cliente é obrigatório.")
        
			else:
				# Se caiu aqui, é porque fone_cli não é só número
				st.error("O campo telefone aceita apenas números (sem espaços ou traços).
                
            #else:
               # st.warning("O nome do cliente é obrigatório.")

# --- 2. STOCK ATUAL & ALERTAS ---
elif choice == "Estoque Atual":
    st.subheader("Status do Inventário em Tempo Real")

    # Executa a busca
    response = supabase.table("produtos").select("*").execute()

    # Verifica se há dados
    if response.data:
        df = pd.DataFrame(response.data)

        # Garante que os nomes das colunas no Pandas estejam corretos
        df = df.rename(columns={
         #   "cod_prd": "ID",
            "produto": "Produto",
            "qnt_prd": "Quantidade",
            "estmin": "Estoque Mínimo"
        })

        # Mostra a tabela limpa
        st.dataframe(df[['Produto', 'Quantidade', 'Estoque Mínimo']], use_container_width=True)


        # Lógica de Alertas
        for _, row in df.iterrows():
            if row['Quantidade'] <= 0:
                st.error(f"🚨 PRODUTO ZERADO: {row['Produto']}")
            elif row['Quantidade'] <= row['Estoque Mínimo']:
                st.warning(f"⚠️ Stock Baixo: {row['Produto']} (Apenas {row['Quantidade']} un)")
    else:
        st.info("Nenhum produto cadastrado no estoque ainda.")

# --- 3. CADASTRO DE FORNECEDOR ---
elif choice == "Cadastrar Fornecedor":
    st.subheader("🚚 Novo Fornecedor")

    # Criamos um formulário para encapsular os campos
    with st.form("form_fornecedor", clear_on_submit=True):
        nome = st.text_input("Nome da Empresa/Vendedor")
        fone_f = st.text_input("Telefone ou E-mail")
        local_f = st.text_input("Endereço")

        # O botão agora é a única porta de entrada para o banco
        submit_button = st.form_submit_button("Salvar Fornecedor")

        # A lógica só roda se o botão for pressionado
        if submit_button:
            if nome:    # Verifica se o nome não está vazio
                supabase.table("fornecedor").insert({"nome_f": nome, "fone_f": fone_f, "local_f": local_f,}).execute()

                st.success(f"Fornecedor {nome} cadastrado com sucesso!")
            else:
                st.warning("O nome do fornecedor é obrigatório.")

# --- 4. ENTRADA DE MATERIAL ---
elif choice == "Entrada (Compra)":
    st.subheader("📥 Registrar Compra")

    # Carregar fornecedores para o selectbox
    forn_data = supabase.table("fornecedor").select("nome_f").execute()
    lista_forn = [f['nome_f'] for f in forn_data.data] if forn_data.data else []

    with st.form("form_entrada"):
        forn_choice = st.selectbox("Selecione o Fornecedor", lista_forn)
        produto_nome = st.text_input("Nome do Produto")
        qtd_entrada = st.number_input("Quantidade Comprada", min_value=1)
        estoque_min = st.number_input("Alerta de estoque mínimo (un)", min_value=1)

        if st.form_submit_button("Confirmar Entrada"):
            # Verifica se produto já existe
            res = supabase.table("produtos").select("*").eq("produto", produto_nome).execute()

            if res.data:
                nova_qtd = res.data[0]['qnt_prd'] + qtd_entrada
                supabase.table("produtos").update({"qnt_prd": nova_qtd}).eq("produto", produto_nome).execute()
            else:
                supabase.table("produtos").insert({"fornecedor": forn_choice, "produto": produto_nome, "qnt_prd": qtd_entrada, "estmin": estoque_min}).execute()

            # Regista histórico
            supabase.table("movimentacoes").insert({
                "data": datetime.now().isoformat(),
                "tipo": "ENTRADA",
                "produto": produto_nome,
                "qnt_prd": qtd_entrada,
                "origem_destino": forn_choice
            }).execute()
            st.success("estoque atualizado com sucesso!")

# --- 5. SAÍDA DE MATERIAL ---
elif choice == "Saída (Uso/Venda)":
    st.subheader("📤 Registrar Uso ou Venda")

    prod_data = supabase.table("produtos").select("produto").gt("qnt_prd", 0).execute()
    lista_prod = [p['produto'] for p in prod_data.data] if prod_data.data else []

    with st.form("form_saida"):
        prod_choice = st.selectbox("Produto a retirar", lista_prod)
        qtd_saida = st.number_input("Quantidade", min_value=1)
        destino = st.text_input("Destino (Ex: Cliente João / OS 452)")

        if st.form_submit_button("Confirmar Saída"):
            res = supabase.table("produtos").select("id", "qnt_prd").eq("produto", prod_choice).execute()
            if res.data and res.data[0]['qnt_prd'] >= qtd_saida:
                nova_qtd = res.data[0]['qnt_prd'] - qtd_saida
                supabase.table("produtos").update({"qnt_prd": nova_qtd}).eq("id", res.data[0]['id']).execute()

                supabase.table("movimentacoes").insert({
                    "data": datetime.now().isoformat(),
                    "tipo": "SAÍDA",
                    "produto": prod_choice,
                    "qnt_prd": qtd_saida,
                    "origem_destino": destino
                }).execute()
                st.success(f"Saída registada!")
            else:
                st.error("Quantidade insuficiente!")
