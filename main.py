import streamlit as st
import pandas as pd 
import requests
from requests.auth import HTTPBasicAuth
import re
from datetime import datetime, date
import io
from PIL import Image

ODATA_URL = st.secrets["odatas"]["ODATA_URL"]

SAP_USER = st.secrets["sap_logon"]["SAP_USER"]
SAP_PASS = st.secrets["sap_logon"]["SAP_PASS"]

st.set_page_config(page_title="Relatorio Fornecedor", layout="wide")

col1, col2 = st.columns([1, 16])
with col1: 
    logo = Image.open("LOGO_USA_ORIGINAL_SEM_FUNDO.png")
    st.image(logo, width=70)

with col2:
    st.title(" Relatório de Fornecedores - 0.1 ")

with st.sidebar:
    st.header(" 🔍 Filtros ")
    tipo_filtro = st.selectbox("Filtrar por:", ["Número da Fazenda", "Nome do Fornecedor"])
    valor_filtro = st.text_input("Digite o valor:", "")

    if st.button("Salvar Filtros"):
        st.session_state["tipo_filtro"] = tipo_filtro
        st.session_state["valor_filtro"] = valor_filtro
        st.success("Filtros salvos! ")

st.subheader("📊 Resultado da Consulta")

if st.button("Consultar SAP"):
    with st.spinner("🔄 Consultando SAP ..."):
        try:
            headers = {
               "Accept": "application/json", 
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