import streamlit as st
import pandas as pd 
import requests
from requests.auth import HTTPBasicAuth
import re
from datetime import datetime, date
import io
import calendar
from PIL import Image

ODATA_URL = st.secrets["odatas"]["ODATA_URL"]

SAP_USER = st.secrets["sap_logon"]["SAP_USER"]
SAP_PASS = st.secrets["sap_logon"]["SAP_PASS"]

def formatar_data_sap(date_str):
    match = re.search(r'/Date\((\d+)\)/', date_str)
    if match:
        timestamp = int(match.group(1)) // 1000
        return datetime.utcfromtimestamp(timestamp).strftime("%d/%m/%Y")
    return date_str

st.set_page_config(page_title="Relatorio Fornecedor", layout="wide")

col1, col2 = st.columns([1, 16])
with col1: 
    logo = Image.open("LOGO_USA_ORIGINAL_SEM_FUNDO.png")
    st.image(logo, width=70)

with col2:
    st.title(" Relatório de Fornecedores - 0.3 ")

if "data_ini" not in st.session_state:
    st.session_state["data_ini"] = date.today().replace(day=1)
if "data_fim" not in st.session_state:
    st.session_state["data_fim"] = date.today().replace()

with st.sidebar:
    st.header(" 🔍 Filtros ")

    # Escolha do mês e ano
    mes = st.selectbox("Selecione o mês:", list(range(1, 13)), format_func=lambda x: calendar.month_name[x])
    ano = st.number_input("Ano:", min_value=2020, max_value=2099, value=2025, step=1)
    
    # Calcula primeiro e último dia do mês selecionado
    primeiro_dia = date(ano, mes, 1)
    ultimo_dia = date(ano, mes, calendar.monthrange(ano, mes)[1])

    
    # Safra estática por enquanto
    periodo = "2025/2026"
    filtro_tipo = st.selectbox("Filtrar por:", ["Chave (Fazenda)", "Contrato (EBELN)"])

    if filtro_tipo == "Chave (Fazenda)":
        filtro_valor = st.text_input("Digite a Chave (ex: FTU100360000):", "")
        header_filtro = {"chave": filtro_valor}
    else:
        filtro_valor = st.text_input("Digite o Contrato (ex: 4600012345):", "")
        header_filtro = {"contrato": filtro_valor}

    st.caption(f"📅 Período calculado: {primeiro_dia.strftime('%d/%m/%Y')} até {ultimo_dia.strftime('%d/%m/%Y')}")


st.subheader("📊 Resultado da Consulta")

if st.button("Consultar SAP"):
    with st.spinner("🔄 Consultando SAP ..."):
        try:
            headers = {
               "Accept": "application/json",
               "periodo": periodo,
               "data_ini": primeiro_dia.strftime("%Y%m%d"),
               "data_fim": ultimo_dia.strftime("%Y%m%d"),
               "x-csrf-token": "fetch"
            }

            response = requests.get(
                ODATA_URL,
                auth=HTTPBasicAuth(SAP_USER, SAP_PASS),
                headers=headers,
                verify=False
            )

            #df = pd.DataFrame(response.json().get("d", {}).get("results", [])) if response.status_code == 200 else pd.DataFrame()

            if response.status_code == 200:
                json_data = response.json()
                dados = json_data.get("d", {}).get("results", [])
                if not dados:
                    st.warning("Nenhum registro retornado pelo SAP.")
                    st.stop()
                if dados:
                    df = pd.DataFrame(dados)
                    df.columns = [col.upper() for col in df.columns]
                    df = df.drop(columns=[col for col in df.columns if "__metadata" in col or col.startswith("__")], errors="ignore")
                st.success(f"{len(df)} registros encontrados.")
                st.dataframe(df)

                with st.expander("📥 Exportar"):
                    try:
                        df_export = df.copy()
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine="openpyxl") as writer:
                            df_export.to_excel(writer, index=False, sheet_name="RelatorioFornecedor")
                        output.seek(0)
                        st.download_button(
                            label="📤 Baixar Excel (.xlsx)",
                            data=output.getvalue(),
                            file_name="relatorio_fornecedor.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                        )

                    except Exception as e:
                        st.error("Erro ao conectar ou processar os dados.")
                        st.exception(e)
            else:
                st.error(f"Erro {response.status_code} ao consultar SAP")
                st.text(response.text)   

        except Exception as e:
            st.error("Erro ao conectar ou processar os dados.")
            st.exception(e)