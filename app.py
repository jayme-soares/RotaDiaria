import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
import matplotlib.colors as mcolors
import sqlite3
import os
import html as html_lib

# Configuração da página do Streamlit
st.set_page_config(page_title="Visualizador de Rotas de Campo", layout="wide")

# --- Autenticação ---


def tela_login():
    st.title("🔒 Acesso Restrito")
    st.info("Solicite a senha ao responsável técnico.")
    senha = st.text_input("Senha de acesso", type="password", key="senha_input")
    if st.button("Entrar"):
        senha_secrets = st.secrets.get("password", "")
        if senha_secrets and senha == senha_secrets:
            st.session_state["authenticated"] = True
            st.rerun()
        st.error("Senha incorreta. Tente novamente.")


if "authenticated" not in st.session_state:
    tela_login()
    st.stop()


# --- Aplicação Principal ---
if not st.session_state.get("authenticated"):
    st.stop()

st.title("📍 Rotas de Equipes em Campo")

if st.sidebar.button("Sair"):
    st.session_state.pop("authenticated", None)
    st.rerun()


DB_PATH = r"C:\Users\CENEGED\Documents\BI_SOC\Bases de dados\soc-marica.db"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRAMITES_PATH = os.path.join(SCRIPT_DIR, "Tramites.xlsx")


def _carregar_local():
    """Fallback: lê do SQLite local (apenas para desenvolvimento)."""
    conn = sqlite3.connect(DB_PATH)
    df_full = pd.read_sql_query("SELECT * FROM base_producao", conn)
    conn.close()

    col_indices = [4, 34, 21, 20, 62, 63, 13, 59, 9, 58, 10]
    col_names = ['Código TdC', 'Equipe', 'Latitude', 'Longitude',
                 'Data Início', 'Data Fim', 'Estado TdC', 'Resultado', 'Tipo TdC',
                 'Causa/Descritivo Resultado', 'Ciclo de trabalho']
    df = df_full.iloc[:, col_indices].copy()
    df.columns = col_names
    return df


def _carregar_gsheet():
    """Lê os dados da Google Sheets (para produção no Cloud)."""
    import gspread
    from google.oauth2.service_account import Credentials

    creds_raw = st.secrets["gsheet_credentials"]
    creds = Credentials.from_service_account_info(
        creds_raw,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    client = gspread.authorize(creds)
    sheet = client.open_by_key(st.secrets["gsheet_id"]).worksheet("dados")
    records = sheet.get_all_records()
    return pd.DataFrame(records)


def _aplicar_tramites(df):
    """Faz merge com Tramites.xlsx local para obter a coluna 'Tramite'."""
    if os.path.exists(TRAMITES_PATH):
        df_tramites = pd.read_excel(TRAMITES_PATH)
        df = df.merge(df_tramites, how='left')
    return df


@st.cache_data(ttl=3600)
def carregar_dados():
    if "gsheet_id" in st.secrets:
        df = _carregar_gsheet()
    else:
        df = _carregar_local()
    df = _aplicar_tramites(df)
    return df


try:
    df = carregar_dados()

    COL_ID = 'Código TdC'
    COL_EQUIPE = 'Equipe'
    COL_LAT = 'Latitude'
    COL_LON = 'Longitude'
    COL_DATA = 'Data Início'
    COL_HORA_INI = 'Data Início'
    COL_HORA_FIM = 'Data Fim'
    COL_STATUS = 'Estado TdC'
    COL_RETORNO = 'Resultado'
    COL_SETOR = 'Tipo TdC'
    COL_TRAMITE = 'Tramite'
    COL_CAUSA = 'Causa/Descritivo Resultado'

    # Dados
    df[COL_LAT] = pd.to_numeric(df[COL_LAT], errors="coerce")
    df[COL_LON] = pd.to_numeric(df[COL_LON], errors="coerce")

    def separar_data_hora(valor):
        if pd.isna(valor):
            return None, None
        texto = str(valor).strip()
        partes = texto.split(" ")
        return partes[0] if len(partes) >= 1 else None, " ".join(partes[1:]) if len(partes) >= 2 else None

    datas = df[COL_DATA].apply(separar_data_hora)
    df["Data_Crua"] = [d[0] for d in datas]
    df["Hora_Inicio_Crua"] = [d[1] for d in datas]

    df["DataHora"] = pd.to_datetime(df["Data_Crua"] + " " + df["Hora_Inicio_Crua"], dayfirst=True, errors="coerce")
    df["Data_BR"] = pd.to_datetime(df["Data_Crua"], dayfirst=True, errors="coerce").dt.strftime("%d/%m/%Y")
    df["Mes"] = pd.to_datetime(df["Data_Crua"], dayfirst=True, errors="coerce").dt.to_period("M").astype(str)

    df[COL_HORA_INI] = df[COL_HORA_INI].apply(lambda x: str(x).split(" ")[-1] if pd.notna(x) else "")
    df[COL_HORA_FIM] = df[COL_HORA_FIM].apply(lambda x: str(x).split(" ")[-1] if pd.notna(x) else "")

    # Filtros
    st.sidebar.header("🔍 Filtros")

    meses_disponiveis = sorted(df["Mes"].dropna().unique().tolist())
    meses_labels = [f"{m.split('-')[1]}/{m.split('-')[0]}" for m in meses_disponiveis]
    mes_map = dict(zip(meses_labels, meses_disponiveis))
    mes_selecionado_label = st.sidebar.selectbox("🗓️ Mês/Ano", meses_labels)
    mes_selecionado = mes_map[mes_selecionado_label]

    df_mes = df[df["Mes"] == mes_selecionado]

    datas_ordenadas = df_mes.dropna(subset=["Data_BR"]).sort_values("DataHora")["Data_BR"].unique().tolist()
    data_selecionada = st.sidebar.selectbox("📅 Selecione a Data", datas_ordenadas)

    df_f1 = df_mes[df_mes["Data_BR"] == data_selecionada]

    st.sidebar.markdown("---")

    setores_disponiveis = sorted(df_f1[COL_SETOR].dropna().unique().tolist())
    todos_setores = st.sidebar.checkbox("Selecionar todos os Setores", value=False)
    if todos_setores:
        setores_selecionados = setores_disponiveis
    else:
        setores_selecionados = st.sidebar.multiselect("🏢 Setores (Tipo TdC)", setores_disponiveis)

    df_f2 = df_f1[df_f1[COL_SETOR].isin(setores_selecionados)]

    equipes_disponiveis = sorted(df_f2[COL_EQUIPE].dropna().unique().tolist())
    todas_equipes = st.sidebar.checkbox("Selecionar todas as Equipes", value=False)
    if todas_equipes:
        equipes_selecionadas = equipes_disponiveis
    else:
        equipes_selecionadas = st.sidebar.multiselect("👷 Equipes", equipes_disponiveis)

    df_f3 = df_f2[df_f2[COL_EQUIPE].isin(equipes_selecionadas)]

    status_disponiveis = sorted(df_f3[COL_STATUS].dropna().unique().tolist())
    todos_status = st.sidebar.checkbox("Selecionar todos os Status", value=False)
    if todos_status:
        status_selecionados = status_disponiveis
    else:
        status_selecionados = st.sidebar.multiselect("✅ Status da Atividade", status_disponiveis)

    df_filtrado = df_f3[df_f3[COL_STATUS].isin(status_selecionados)]

    df_filtrado = df_filtrado.dropna(subset=[COL_LAT, COL_LON])
    df_filtrado = df_filtrado.sort_values(by=[COL_EQUIPE, "DataHora"])

    if df_filtrado.empty:
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        centro_lat = df_filtrado[COL_LAT].mean()
        centro_lon = df_filtrado[COL_LON].mean()
        mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)

        cores_equipe = ["#1f77b4", "#9467bd", "#ff7f0e", "#8c564b", "#e377c2", "#17becf", "#7f7f7f", "#bcbd22"]

        todos_os_setores_planilha = sorted(df_filtrado[COL_SETOR].dropna().unique().tolist())
        lista_cores_hex = list(mcolors.TABLEAU_COLORS.values()) + list(mcolors.CSS4_COLORS.values())
        cores_setor_dict = {setor: lista_cores_hex[i % len(lista_cores_hex)] for i, setor in enumerate(todos_os_setores_planilha)}

        equipes_filtradas = df_filtrado[COL_EQUIPE].unique()

        for index, nome_equipe in enumerate(equipes_filtradas):
            dados_equipe = df_filtrado[df_filtrado[COL_EQUIPE] == nome_equipe]
            cor_linha_equipe = cores_equipe[index % len(cores_equipe)]

            coordenadas_rota = dados_equipe[[COL_LAT, COL_LON]].values.tolist()
            if len(coordenadas_rota) > 1:
                folium.PolyLine(
                    coordenadas_rota, color=cor_linha_equipe, weight=4, opacity=0.8,
                    tooltip=f"Rota: {nome_equipe}"
                ).add_to(mapa)

                folium.Marker(
                    location=coordenadas_rota[0],
                    tooltip=f"🟢 INÍCIO DA ROTA - {nome_equipe}",
                    icon=folium.Icon(color="green", icon="play")
                ).add_to(mapa)

                folium.Marker(
                    location=coordenadas_rota[-1],
                    tooltip=f"🏁 FIM DA ROTA - {nome_equipe}",
                    icon=folium.Icon(color="black", icon="stop")
                ).add_to(mapa)

            for _, row in dados_equipe.iterrows():
                codigo_td = html_lib.escape(str(row[COL_ID]).split(".")[0], quote=True)
                equipe_html = html_lib.escape(str(row[COL_EQUIPE]), quote=True)
                data_html = html_lib.escape(str(row["Data_BR"]), quote=True)
                setor_html = html_lib.escape(str(row[COL_SETOR]), quote=True)
                status_html = html_lib.escape(str(row[COL_STATUS]), quote=True)
                retorno_html = html_lib.escape(str(row[COL_RETORNO]), quote=True)
                hora_ini_html = html_lib.escape(str(row[COL_HORA_INI]), quote=True)
                hora_fim_html = html_lib.escape(str(row[COL_HORA_FIM]), quote=True)
                tramite_html = html_lib.escape(str(row.get(COL_TRAMITE, "") or ""), quote=True)
                causa_html = html_lib.escape(str(row.get(COL_CAUSA, "") or ""), quote=True)

                retorno_texto = str(row[COL_RETORNO]).strip().lower()
                if retorno_texto == "realizado":
                    cor_fundo_retorno = "#2ca02c"
                elif retorno_texto in ["não realizado", "nao realizado"]:
                    cor_fundo_retorno = "#d62728"
                else:
                    cor_fundo_retorno = "#7f7f7f"

                cor_borda_setor = cores_setor_dict.get(row[COL_SETOR], "#ffffff")

                tabela_html = f"""
                <div style="width: 260px; font-family: Arial, sans-serif;">
                    <h4 style="margin-top: 0; color: {cor_linha_equipe};">{equipe_html}</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <tr style="border-bottom: 1px solid #ddd; background-color: #f8f9fa;">
                            <td style="padding: 4px; font-weight: bold;">Código TdC:</td>
                            <td style="padding: 4px;">{codigo_td}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Data:</td>
                            <td style="padding: 4px;">{data_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Setor:</td>
                            <td style="padding: 4px;">{setor_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Status:</td>
                            <td style="padding: 4px;">{status_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Retorno:</td>
                            <td style="padding: 4px; font-weight: bold; color: {cor_fundo_retorno};">{retorno_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Início:</td>
                            <td style="padding: 4px;">{hora_ini_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Fim:</td>
                            <td style="padding: 4px;">{hora_fim_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Trâmite:</td>
                            <td style="padding: 4px;">{tramite_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Causa/Desc. Resultado:</td>
                            <td style="padding: 4px;">{causa_html}</td>
                        </tr>
                    </table>
                </div>
                """
                popup = folium.Popup(tabela_html, max_width=320)

                icone_customizado = folium.DivIcon(
                    html=f"""
                    <div style="
                        background-color: {cor_fundo_retorno};
                        color: white;
                        border-radius: 50%;
                        width: 30px;
                        height: 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 10px;
                        border: 4px solid {cor_borda_setor};
                        box-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    ">
                        {codigo_td}
                    </div>
                    """
                )

                folium.Marker(
                    location=[row[COL_LAT], row[COL_LON]],
                    popup=popup,
                    icon=icone_customizado
                ).add_to(mapa)

        st.markdown("""
        **Legenda do Mapa:** 📍 Fundo Verde: Realizado | 📍 Fundo Vermelho: Não Realizado | 🟢 Pino: Início da Rota | 🏁 Pino Preto: Fim da Rota
        *(A borda externa dos círculos muda de cor de acordo com o Setor/Tipo TdC)*
        """)

        st_folium(mapa, width=1200, height=650)

        with st.expander("Ver Tabela de Dados Filtrados"):
            st.dataframe(df_filtrado[[COL_ID, COL_EQUIPE, "Data_BR", COL_HORA_INI, COL_SETOR, COL_RETORNO]], use_container_width=True)

except Exception as e:
    import traceback
    st.error(f"Erro interno: {e}")
    st.code(traceback.format_exc())
