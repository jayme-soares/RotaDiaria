import streamlit as st
import pandas as pd
import folium
import streamlit.components.v1 as components
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

st.title("📍 Rotas de Equipes")

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
    """Lê dados das abas do Google Sheets (produção no Cloud)."""
    import gspread
    from google.oauth2.service_account import Credentials

    def _valores_para_df(valores):
        if not valores:
            return pd.DataFrame()
        headers = valores[0]
        rows = valores[1:] if len(valores) > 1 else []
        width = len(headers)
        rows_ajustadas = [r[:width] + [""] * max(0, width - len(r)) for r in rows]
        return pd.DataFrame(rows_ajustadas, columns=headers)

    creds_raw = st.secrets["gsheet_credentials"]
    creds = Credentials.from_service_account_info(
        creds_raw,
        scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"]
    )
    client = gspread.authorize(creds)
    spreadsheet = client.open_by_key(st.secrets["gsheet_id"])

    worksheets = {ws.title: ws for ws in spreadsheet.worksheets()}
    dados_values = worksheets["dados"].get_all_values() if "dados" in worksheets else []
    designados_values = worksheets["designados"].get_all_values() if "designados" in worksheets else []
    coordenadas_values = worksheets["coordenadas"].get_all_values() if "coordenadas" in worksheets else []

    df_dados = _valores_para_df(dados_values)
    df_designados = _padronizar_designados(_valores_para_df(designados_values))
    df_coordenadas = _padronizar_coordenadas(_valores_para_df(coordenadas_values))
    return df_dados, df_designados, df_coordenadas


def _aplicar_tramites(df):
    """Faz merge com Tramites.xlsx local para obter a coluna 'Tramite'."""
    if os.path.exists(TRAMITES_PATH):
        df_tramites = pd.read_excel(TRAMITES_PATH)
        df = df.merge(df_tramites, how='left')
    return df


def _normalizar_nome_coluna(nome):
    texto = str(nome).strip().lower()
    mapa = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc")
    texto = texto.translate(mapa)
    return "".join(ch for ch in texto if ch.isalnum())


def _selecionar_coluna(df, aliases):
    colunas_norm = {_normalizar_nome_coluna(c): c for c in df.columns}
    for alias in aliases:
        col = colunas_norm.get(_normalizar_nome_coluna(alias))
        if col:
            return col
    return None


def _selecionar_coluna_fuzzy(df, inclui=None, exclui=None):
    inclui = inclui or []
    exclui = exclui or []
    for col in df.columns:
        norm = _normalizar_nome_coluna(col)
        if all(token in norm for token in inclui) and all(token not in norm for token in exclui):
            return col
    return None


def _parse_data_flexivel(serie):
    data_dmy = pd.to_datetime(serie, dayfirst=True, errors="coerce")
    faltantes = data_dmy.isna()
    if faltantes.any():
        data_ymd = pd.to_datetime(serie[faltantes], dayfirst=False, errors="coerce")
        data_dmy.loc[faltantes] = data_ymd
    return data_dmy


def _normalizar_texto_filtro(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip().lower()
    mapa = str.maketrans("áàâãäéèêëíìîïóòôõöúùûüç", "aaaaaeeeeiiiiooooouuuuc")
    texto = texto.translate(mapa)
    return "".join(ch for ch in texto if ch.isalnum())


def _normalizar_chave_codigo(valor):
    if pd.isna(valor):
        return ""
    texto = str(valor).strip()
    if texto.endswith(".0"):
        texto = texto[:-2]
    return _normalizar_nome_coluna(texto)


def _colunas_padrao_designados():
    return ['Código TdC', 'Código Cliente', 'Equipe Designada', 'Tipo Serviço', 'Estado', 'Data', 'Endereço', 'Latitude', 'Longitude']


def _padronizar_designados(df_raw):
    if df_raw.empty:
        return pd.DataFrame(columns=_colunas_padrao_designados())

    col_id = _selecionar_coluna(df_raw, ["Código TdC", "codigo_tdc", "codigo tdc"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["codigo", "tdc"])
    col_equipe = _selecionar_coluna(df_raw, ["Equipe", "Recurso", "Equipe Designada", "recurso/equipe", "recursoequipe"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["equipe"])
    col_tipo = _selecionar_coluna(df_raw, ["Tipo TdC", "Setor", "Tipo Serviço", "tipo_servico", "tipo de servico"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["tipo"])
    col_estado = _selecionar_coluna(df_raw, ["Estado", "Stato"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["estado"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["stato"])
    col_data = _selecionar_coluna(
        df_raw,
        [
            "Data início Escalonamento", "Data Inicio Escalonamento", "data_inicio_escalonamento",
            "Data", "Data Início", "Data início execução", "data_inicio_execucao", "data início"
        ]
    ) or _selecionar_coluna_fuzzy(df_raw, inclui=["datainicioescalonamento"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["data"])
    col_cliente = _selecionar_coluna(df_raw, ["Código Cliente", "Codigo Cliente", "cod_cliente", "cliente_codigo", "Cliente ID"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["codigo", "cliente"])
    col_endereco = _selecionar_coluna(df_raw, ["Endereço", "Endereco", "Logradouro", "endereco completo"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["endere"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["logradouro"])
    col_lat = _selecionar_coluna(df_raw, ["Latitude", "lat"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["lat"])
    col_lon = _selecionar_coluna(df_raw, ["Longitude", "lon", "long"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["lon"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["long"])

    df = pd.DataFrame()
    df['Código TdC'] = df_raw[col_id] if col_id else ""
    df['Código Cliente'] = df_raw[col_cliente] if col_cliente else ""
    df['Equipe Designada'] = df_raw[col_equipe] if col_equipe else ""
    df['Tipo Serviço'] = df_raw[col_tipo] if col_tipo else ""
    df['Estado'] = df_raw[col_estado] if col_estado else ""
    df['Data'] = df_raw[col_data] if col_data else ""
    df['Endereço'] = df_raw[col_endereco] if col_endereco else ""
    df['Latitude'] = pd.to_numeric(df_raw[col_lat], errors="coerce") if col_lat else pd.NA
    df['Longitude'] = pd.to_numeric(df_raw[col_lon], errors="coerce") if col_lon else pd.NA
    return df


def _carregar_designados_local():
    conn = sqlite3.connect(DB_PATH)
    try:
        df_raw = pd.read_sql_query("SELECT * FROM base_designados", conn)
    except pd.errors.DatabaseError:
        return pd.DataFrame(columns=_colunas_padrao_designados())
    finally:
        conn.close()
    return _padronizar_designados(df_raw)


def _colunas_padrao_coordenadas():
    return ['Instalação', 'Latitude', 'Longitude']


def _padronizar_coordenadas(df_raw):
    if df_raw.empty:
        return pd.DataFrame(columns=_colunas_padrao_coordenadas())

    col_instalacao = _selecionar_coluna(df_raw, ["Instalação", "Instalacao", "codigo_cliente", "Código Cliente"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["instala"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["cliente"])
    col_lat = _selecionar_coluna(df_raw, ["Latitude", "lat"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["lat"])
    col_lon = _selecionar_coluna(df_raw, ["Longitude", "lon", "long"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["lon"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["long"])

    df = pd.DataFrame()
    df['Instalação'] = df_raw[col_instalacao] if col_instalacao else ""
    df['Latitude'] = pd.to_numeric(df_raw[col_lat], errors="coerce") if col_lat else pd.NA
    df['Longitude'] = pd.to_numeric(df_raw[col_lon], errors="coerce") if col_lon else pd.NA
    return df


def _carregar_coordenadas_local():
    conn = sqlite3.connect(DB_PATH)
    try:
        df_raw = pd.read_sql_query("SELECT * FROM base_coordenadas", conn)
    except pd.errors.DatabaseError:
        return pd.DataFrame(columns=_colunas_padrao_coordenadas())
    finally:
        conn.close()
    return _padronizar_coordenadas(df_raw)


def _vincular_coordenadas_designados(df_designados, df_coordenadas):
    if df_designados.empty or df_coordenadas.empty:
        return df_designados

    designados = df_designados.copy()
    coordenadas = df_coordenadas.copy()

    designados["_chave_cliente"] = designados["Código Cliente"].apply(_normalizar_chave_codigo)
    coordenadas["_chave_cliente"] = coordenadas["Instalação"].apply(_normalizar_chave_codigo)

    coords_validas = coordenadas[
        (coordenadas["_chave_cliente"] != "") &
        coordenadas["Latitude"].notna() &
        coordenadas["Longitude"].notna()
    ].copy()
    coords_validas = coords_validas.drop_duplicates(subset=["_chave_cliente"], keep="first")
    coords_validas = coords_validas.rename(columns={"Latitude": "Latitude Coord", "Longitude": "Longitude Coord"})

    df_merge = designados.merge(
        coords_validas[["_chave_cliente", "Latitude Coord", "Longitude Coord"]],
        on="_chave_cliente",
        how="left"
    )
    df_merge["Latitude"] = df_merge["Latitude"].fillna(df_merge["Latitude Coord"])
    df_merge["Longitude"] = df_merge["Longitude"].fillna(df_merge["Longitude Coord"])
    return df_merge.drop(columns=["_chave_cliente", "Latitude Coord", "Longitude Coord"])


@st.cache_data(ttl=3600)
def carregar_dados():
    if "gsheet_id" in st.secrets:
        df, df_designados, df_coordenadas = _carregar_gsheet()
    else:
        df = _carregar_local()
        df_designados = _carregar_designados_local()
        df_coordenadas = _carregar_coordenadas_local()
    df = _aplicar_tramites(df)
    return df, df_designados, df_coordenadas


try:
    df, df_designados, df_coordenadas = carregar_dados()

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
    COL_D_ID = 'Código TdC'
    COL_D_CLIENTE = 'Código Cliente'
    COL_D_EQUIPE = 'Equipe Designada'
    COL_D_TIPO = 'Tipo Serviço'
    COL_D_ESTADO = 'Estado'
    COL_D_DATA = 'Data'
    COL_D_ENDERECO = 'Endereço'
    COL_D_LAT = 'Latitude'
    COL_D_LON = 'Longitude'

    # Dados
    df[COL_LAT] = pd.to_numeric(df[COL_LAT], errors="coerce")
    df[COL_LON] = pd.to_numeric(df[COL_LON], errors="coerce")
    df_designados[COL_D_LAT] = pd.to_numeric(df_designados[COL_D_LAT], errors="coerce")
    df_designados[COL_D_LON] = pd.to_numeric(df_designados[COL_D_LON], errors="coerce")
    df_designados = _vincular_coordenadas_designados(df_designados, df_coordenadas)
    df_designados[COL_D_LAT] = pd.to_numeric(df_designados[COL_D_LAT], errors="coerce")
    df_designados[COL_D_LON] = pd.to_numeric(df_designados[COL_D_LON], errors="coerce")

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

    df_designados["DataHora"] = _parse_data_flexivel(df_designados[COL_D_DATA])
    df_designados["Data_BR"] = df_designados["DataHora"].dt.strftime("%d/%m/%Y")
    df_designados["Mes"] = df_designados["DataHora"].dt.to_period("M").astype(str)

    df[COL_HORA_INI] = df[COL_HORA_INI].apply(lambda x: str(x).split(" ")[-1] if pd.notna(x) else "")
    df[COL_HORA_FIM] = df[COL_HORA_FIM].apply(lambda x: str(x).split(" ")[-1] if pd.notna(x) else "")

    # Filtros
    st.sidebar.header("🔍 Filtros")

    meses_disponiveis = sorted(
        set(df["Mes"].dropna().tolist() + df_designados["Mes"].dropna().tolist()) - {"NaT"}
    )
    meses_labels = [f"{m.split('-')[1]}/{m.split('-')[0]}" for m in meses_disponiveis]
    mes_map = dict(zip(meses_labels, meses_disponiveis))
    mes_selecionado_label = st.sidebar.selectbox("🗓️ Mês/Ano", meses_labels)
    mes_selecionado = mes_map[mes_selecionado_label]

    df_mes = df[df["Mes"] == mes_selecionado]
    df_designados_mes = df_designados[df_designados["Mes"] == mes_selecionado]

    datas_ordenadas = sorted(
        set(df_mes.dropna(subset=["Data_BR"])["Data_BR"].tolist() + df_designados_mes.dropna(subset=["Data_BR"])["Data_BR"].tolist()),
        key=lambda x: pd.to_datetime(x, dayfirst=True, errors="coerce")
    )
    data_selecionada = st.sidebar.selectbox("📅 Selecione a Data", datas_ordenadas)

    df_f1 = df_mes[df_mes["Data_BR"] == data_selecionada]
    df_designados_f1 = df_designados_mes[df_designados_mes["Data_BR"] == data_selecionada]

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
    todos_status = st.sidebar.checkbox("Selecionar todos os Status", value=True)
    if todos_status:
        status_selecionados = status_disponiveis
    else:
        status_selecionados = st.sidebar.multiselect("✅ Status da Atividade", status_disponiveis)

    df_filtrado = df_f3[df_f3[COL_STATUS].isin(status_selecionados)]

    df_filtrado = df_filtrado.dropna(subset=[COL_LAT, COL_LON])
    df_filtrado = df_filtrado.sort_values(by=[COL_EQUIPE, "DataHora"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🗂️ Designados")
    exibir_designados = st.sidebar.checkbox("Exibir camada de designados", value=True)

    # Designados seguem os filtros existentes: data selecionada + equipes selecionadas.
    # Não aplicamos filtro por setor/tipo para preservar todos os designados da equipe no dia.
    equipes_norm = {_normalizar_texto_filtro(e) for e in equipes_selecionadas if str(e).strip()}
    df_designados_tmp = df_designados_f1.copy()
    df_designados_tmp["_equipe_norm"] = df_designados_tmp[COL_D_EQUIPE].apply(_normalizar_texto_filtro)
    if equipes_norm:
        df_designados_filtrado = df_designados_tmp[
            df_designados_tmp["_equipe_norm"].apply(
                lambda equipe: any(
                    equipe == alvo or equipe.startswith(alvo) or alvo.startswith(equipe)
                    for alvo in equipes_norm
                )
            )
        ].drop(columns=["_equipe_norm"])
    else:
        df_designados_filtrado = df_designados_tmp.iloc[0:0].drop(columns=["_equipe_norm"])

    estados_excluidos = {"esitato", "inesecuzione"}
    df_designados_filtrado["_estado_norm"] = df_designados_filtrado[COL_D_ESTADO].apply(_normalizar_nome_coluna)
    df_designados_filtrado = df_designados_filtrado[
        ~df_designados_filtrado["_estado_norm"].isin(estados_excluidos)
    ].drop(columns=["_estado_norm"])
    total_designados_filtrados = len(df_designados_filtrado)
    designados_com_coord = 0
    if exibir_designados and not df_designados_filtrado.empty:
        designados_com_coord = int(df_designados_filtrado[[COL_D_LAT, COL_D_LON]].notna().all(axis=1).sum())
        df_designados_filtrado = df_designados_filtrado.dropna(subset=[COL_D_LAT, COL_D_LON])

    if df_filtrado.empty and (not exibir_designados or df_designados_filtrado.empty):
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        latitudes = []
        longitudes = []
        if not df_filtrado.empty:
            latitudes.extend(df_filtrado[COL_LAT].tolist())
            longitudes.extend(df_filtrado[COL_LON].tolist())
        if exibir_designados and not df_designados_filtrado.empty:
            latitudes.extend(df_designados_filtrado[COL_D_LAT].tolist())
            longitudes.extend(df_designados_filtrado[COL_D_LON].tolist())

        centro_lat = sum(latitudes) / len(latitudes)
        centro_lon = sum(longitudes) / len(longitudes)
        mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)
        camada_exec = folium.FeatureGroup(name="✅ Serviços executados", show=True)
        camada_designados = folium.FeatureGroup(name="🗂️ Serviços designados", show=True)

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
                ).add_to(camada_exec)

                folium.Marker(
                    location=coordenadas_rota[0],
                    tooltip=f"🟢 INÍCIO DA ROTA - {nome_equipe}",
                    icon=folium.Icon(color="green", icon="play")
                ).add_to(camada_exec)

                folium.Marker(
                    location=coordenadas_rota[-1],
                    tooltip=f"🏁 FIM DA ROTA - {nome_equipe}",
                    icon=folium.Icon(color="black", icon="stop")
                ).add_to(camada_exec)

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
                ).add_to(camada_exec)

        if exibir_designados and not df_designados_filtrado.empty:
            for _, row in df_designados_filtrado.iterrows():
                codigo_td = html_lib.escape(str(row[COL_D_ID]).split(".")[0], quote=True)
                equipe_html = html_lib.escape(str(row[COL_D_EQUIPE]), quote=True)
                data_html = html_lib.escape(str(row["Data_BR"]), quote=True)
                tipo_html = html_lib.escape(str(row[COL_D_TIPO]), quote=True)
                endereco_html = html_lib.escape(str(row[COL_D_ENDERECO]), quote=True)

                popup_designado_html = f"""
                <div style="width: 260px; font-family: Arial, sans-serif;">
                    <h4 style="margin-top: 0; color: #7f7f7f;">Serviço Designado</h4>
                    <table style="width: 100%; border-collapse: collapse; font-size: 12px;">
                        <tr style="border-bottom: 1px solid #ddd; background-color: #f8f9fa;">
                            <td style="padding: 4px; font-weight: bold;">Código TdC:</td>
                            <td style="padding: 4px;">{codigo_td}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Equipe:</td>
                            <td style="padding: 4px;">{equipe_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Data:</td>
                            <td style="padding: 4px;">{data_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Tipo Serviço:</td>
                            <td style="padding: 4px;">{tipo_html}</td>
                        </tr>
                        <tr style="border-bottom: 1px solid #ddd;">
                            <td style="padding: 4px; font-weight: bold;">Endereço:</td>
                            <td style="padding: 4px;">{endereco_html}</td>
                        </tr>
                    </table>
                </div>
                """
                popup_designado = folium.Popup(popup_designado_html, max_width=320)
                icone_designado = folium.DivIcon(
                    html=f"""
                    <div style="
                        background-color: #7f7f7f;
                        color: white;
                        border-radius: 50%;
                        width: 30px;
                        height: 30px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        font-weight: bold;
                        font-size: 10px;
                        border: 3px solid #f1c40f;
                        box-shadow: 2px 2px 4px rgba(0,0,0,0.5);
                    ">
                        {codigo_td}
                    </div>
                    """
                )

                folium.Marker(
                    location=[row[COL_D_LAT], row[COL_D_LON]],
                    popup=popup_designado,
                    tooltip=f"Designado: {codigo_td}",
                    icon=icone_designado
                ).add_to(camada_designados)

        camada_exec.add_to(mapa)
        if exibir_designados:
            camada_designados.add_to(mapa)
        folium.LayerControl(collapsed=False).add_to(mapa)

        st.markdown("""
        **Legenda do Mapa:** 📍 Fundo Verde: Realizado | 📍 Fundo Vermelho: Não Realizado | ⚪ Fundo Cinza: Designado |
        🟢 Pino: Início da Rota | 🏁 Pino Preto: Fim da Rota
        *(A borda externa dos círculos muda de cor de acordo com o Setor/Tipo TdC)*
        """)
        if exibir_designados:
            st.caption(f"Designados filtrados: {total_designados_filtrados} | Com coordenadas: {designados_com_coord}")

        components.html(mapa.get_root().render(), height=650, scrolling=False)

        with st.expander("Ver Tabela de Dados Filtrados"):
            st.dataframe(df_filtrado[[COL_ID, COL_EQUIPE, "Data_BR", COL_HORA_INI, COL_SETOR, COL_RETORNO]], use_container_width=True)

        if exibir_designados:
            with st.expander("Ver Tabela de Serviços Designados"):
                st.dataframe(
                    df_designados_filtrado[[COL_D_ID, COL_D_EQUIPE, "Data_BR", COL_D_TIPO, COL_D_ENDERECO]],
                    use_container_width=True
                )

except Exception as e:
    st.error("Erro interno ao processar os dados.")
