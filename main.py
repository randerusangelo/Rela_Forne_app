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

            df = pd.DataFrame(response.json().get("d", {}).get("results", [])) if response.status_code == 200 else pd.DataFrame()

            if not df.empty:
                df.columns = [col.upper() for col in df.columns]
                df = df.drop(columns=[col for col in df.columns if "__METADATA" in col or col.startswith("__")], errors="ignore")
                
            elif not df.empty:
                df_export = df.copy()
            else:
                st.error("Nenhum dado foi encontrado")
                st.stop()


            df_export = df_export.rename(columns={
                "Chave": "Fazenda",
                "QuantTon": "QuantTon",
                "Periodo": "Periodo",
            })

            if not df_export.empty:
                with st.expander("📥 Exportar"):
                    output = io.BytesIO()
                    with pd.ExcelWriter(output, engine="openpyxl") as writer:
                        df_export.to_excel(writer, index=False, sheet_name="Relatorio_Fornecedor")
                    output.seek(0)

                    st.download_button(
                        Label= "📤 Baixar Planilha Excel (.xlsx)",
                        data=output.getvalue(),
                        file_name="relatorio_fornecedor.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

        except Exception as e:
            st.error("Erro ao conectar ou processar os dados.")
            st.exception(e)