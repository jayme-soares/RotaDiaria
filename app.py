import streamlit as st
import pandas as pd
import folium
import streamlit.components.v1 as components
from branca.element import Element
import matplotlib.colors as mcolors
import sqlite3
import os
import base64
import time
import uuid
import requests
import html as html_lib
try:
    from streamlit_autorefresh import st_autorefresh
except Exception:
    def st_autorefresh(*args, **kwargs):
        return 0

# Configuração da página do Streamlit
st.set_page_config(
    page_title="MAGO",
    page_icon=os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "logos", "Icon.png"),
    layout="wide"
)

DB_PATH = r"C:\Users\CENEGED\Documents\BI_SOC\Bases de dados\soc-marica.db"
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TRAMITES_PATH = os.path.join(SCRIPT_DIR, "Tramites.xlsx")
LOGOS_DIR = os.path.join(SCRIPT_DIR, "src", "logos")

LOGO_FULL_LIGHT_PATH = os.path.join(LOGOS_DIR, "Full-light.png")
LOGO_FULL_DARK_PATH = os.path.join(LOGOS_DIR, "Full-dark.png")
LOGO_LIGHT_PATH = os.path.join(LOGOS_DIR, "Logo_light.png")
LOGO_DARK_PATH = os.path.join(LOGOS_DIR, "Logo-dark.png")
LOGO_ICON_PATH = os.path.join(LOGOS_DIR, "Icon.png")
INTRO_WEBM_PATH = os.path.join(LOGOS_DIR, "intro.webm")
INTRO_MP4_PATH = os.path.join(LOGOS_DIR, "intro.mp4")

SETORES_VALIDOS = ["SOC", "NEGOCIACAO"]
SETORES_LABEL = {"SOC": "SOC", "NEGOCIACAO": "Negociação"}


@st.cache_data(show_spinner=False)
def _arquivo_para_data_uri(path):
    if not os.path.exists(path):
        return ""
    with open(path, "rb") as f:
        encoded = base64.b64encode(f.read()).decode("utf-8")
    ext = os.path.splitext(path)[1].lower()
    mime_map = {
        ".png": "image/png",
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".webm": "video/webm",
        ".mp4": "video/mp4",
    }
    mime = mime_map.get(ext, "application/octet-stream")
    return f"data:{mime};base64,{encoded}"


def _render_logo_tema(light_path, dark_path, max_width=440, container=None):
    light_uri = _arquivo_para_data_uri(light_path)
    dark_uri = _arquivo_para_data_uri(dark_path)
    if not light_uri and not dark_uri:
        return False
    if not light_uri:
        light_uri = dark_uri
    if not dark_uri:
        dark_uri = light_uri

    target = container if container is not None else st
    target.markdown(
        f"""
        <style>
        .rd-logo-wrap {{
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin: .2rem 0 1rem 0;
        }}
        .rd-logo-wrap img {{
            width: min(96vw, {int(max_width)}px);
            height: auto;
        }}
        .rd-logo-dark {{ display: none; }}
        html[data-theme="dark"] .rd-logo-light {{ display: none; }}
        html[data-theme="dark"] .rd-logo-dark {{ display: block; }}
        </style>
        <div class="rd-logo-wrap">
            <img class="rd-logo-light" src="{light_uri}" alt="Logo da aplicação">
            <img class="rd-logo-dark" src="{dark_uri}" alt="Logo da aplicação">
        </div>
        """,
        unsafe_allow_html=True,
    )
    return True


def _render_sidebar_icon(container):
    icon_uri = _arquivo_para_data_uri(LOGO_ICON_PATH)
    if not icon_uri:
        container.empty()
        return
    container.markdown(
        f"""
        <div style="display:flex; justify-content:center; margin:-70px 0 0 0; pointer-events:none;">
            <img src="{icon_uri}" alt="Ícone" style="width:100px; height:100px; border-radius:10px; pointer-events:none;" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def _render_icono_sidebar_recolhida():
    icon_uri = _arquivo_para_data_uri(LOGO_ICON_PATH)
    if not icon_uri:
        return
    st.markdown(
        f"""
        <style>
        .rd-corner-icon {{
            position: fixed;
            top: 0.55rem;
            left: 3.2rem;
            z-index: 10010;
            display: none;
            align-items: center;
            justify-content: center;
            pointer-events: none;
        }}
        .rd-corner-icon img {{
            width: 50px;
            height: 50px;
            border-radius: 8px;
            pointer-events: none;
        }}
        html:has(section[data-testid="stSidebar"][aria-expanded="false"]) .rd-corner-icon {{
            display: flex;
        }}
        html:has(section[data-testid="stSidebar"][aria-expanded="true"]) .rd-corner-icon {{
            display: none;
        }}
        </style>
        <div class="rd-corner-icon">
            <img src="{icon_uri}" alt="Ícone da aplicação" />
        </div>
        """,
        unsafe_allow_html=True,
    )


def _obter_intro_uri():
    if os.path.exists(INTRO_MP4_PATH):
        return _arquivo_para_data_uri(INTRO_MP4_PATH)
    if os.path.exists(INTRO_WEBM_PATH):
        return _arquivo_para_data_uri(INTRO_WEBM_PATH)
    return ""


def _obter_loading_uri():
    if os.path.exists(INTRO_WEBM_PATH):
        return _arquivo_para_data_uri(INTRO_WEBM_PATH)
    if os.path.exists(INTRO_MP4_PATH):
        return _arquivo_para_data_uri(INTRO_MP4_PATH)
    return ""


def _render_intro_tela_cheia():
    intro_uri = _obter_intro_uri()
    if not intro_uri:
        return False
    st.markdown(
        f"""
        <style>
        .rd-intro-overlay {{
            position: fixed;
            inset: 0;
            z-index: 10050;
            background: #000;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .rd-intro-overlay video {{
            width: 100vw;
            height: 100vh;
            object-fit: cover;
        }}
        </style>
        <div class="rd-intro-overlay">
            <video autoplay muted playsinline>
                <source src="{intro_uri}">
            </video>
        </div>
        """,
        unsafe_allow_html=True,
    )
    return True


def _render_loading_animado(container=None):
    intro_uri = _obter_loading_uri()
    logo_light = _arquivo_para_data_uri(LOGO_LIGHT_PATH) or _arquivo_para_data_uri(LOGO_FULL_LIGHT_PATH)
    logo_dark = _arquivo_para_data_uri(LOGO_DARK_PATH) or _arquivo_para_data_uri(LOGO_FULL_DARK_PATH)
    if not logo_light and not logo_dark and not intro_uri:
        return

    target = container if container is not None else st
    target.markdown(
        f"""
        <style>
        .rd-loading-overlay-bg {{
            position: fixed;
            inset: 0;
            z-index: 10030;
            background: #000;
            opacity: .6;
        }}
        .rd-loading-logo-wrap {{
            position: relative;
            display: flex;
            justify-content: center;
            align-items: center;
            width: 100%;
            margin: .2rem 0 1rem 0;
            z-index: 10041;
        }}
        .rd-loading-logo-wrap video,
        .rd-loading-logo-wrap img {{
            width: min(96vw, 180px);
            height: auto;
            filter: drop-shadow(0 4px 16px rgba(0,0,0,.45));
        }}
        .rd-loading-dark {{ display: none; }}
        html[data-theme="dark"] .rd-loading-light {{ display: none; }}
        html[data-theme="dark"] .rd-loading-dark {{ display: block; }}
        </style>
        <div class="rd-loading-overlay-bg"></div>
        <div class="rd-loading-logo-wrap">
            {
                f'<video autoplay muted loop playsinline><source src="{intro_uri}"></video>'
                if intro_uri else f'<img class="rd-loading-light" src="{logo_light}" alt="Carregando" /><img class="rd-loading-dark" src="{logo_dark}" alt="Carregando" />'
            }
        </div>
        """,
        unsafe_allow_html=True,
    )


def _setores_para_storage(setores):
    setores_norm = [s for s in setores if s in SETORES_VALIDOS]
    return ",".join(dict.fromkeys(setores_norm))


def _setores_do_storage(valor):
    if not valor:
        return []
    setores = [s.strip().upper() for s in str(valor).split(",") if str(s).strip()]
    return [s for s in setores if s in SETORES_VALIDOS]


def _setor_label(valor):
    if valor is None:
        return ""
    return SETORES_LABEL.get(str(valor), str(valor))


def _formatar_duracao_segundos(total_segundos):
    try:
        segundos = int(total_segundos)
    except Exception:
        return ""
    if segundos < 0:
        segundos = 0
    horas = segundos // 3600
    minutos = (segundos % 3600) // 60
    segs = segundos % 60
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"


def _render_tempo_logado_realtime(session_started_at):
    try:
        ts = int(session_started_at)
    except Exception:
        ts = int(time.time())
    components.html(
        f"""
        <div style="font-size:0.86rem; color: grey; margin:.2rem 0 .35rem 0;">
            Tempo logado: <strong id="rd-session-clock">00:00:00</strong>
        </div>
        <script>
          const startedAt = {ts};
          function pad(n) {{ return String(n).padStart(2, "0"); }}
          function tick() {{
            const now = Math.floor(Date.now()/1000);
            const elapsed = Math.max(0, now - startedAt);
            const h = Math.floor(elapsed / 3600);
            const m = Math.floor((elapsed % 3600) / 60);
            const s = elapsed % 60;
            const el = document.getElementById("rd-session-clock");
            if (el) el.textContent = `${{pad(h)}}:${{pad(m)}}:${{pad(s)}}`;
          }}
          tick();
          setInterval(tick, 1000);
        </script>
        """,
        height=28,
        scrolling=False,
    )


def _supabase_config():
    return {
        "url": st.secrets.get("supabase_url", "").rstrip("/"),
        "anon_key": st.secrets.get("supabase_anon_key", ""),
        "service_key": st.secrets.get("supabase_service_role_key", ""),
        "admin_emails": [
            e.strip().lower()
            for e in str(st.secrets.get("auth_admin_emails", "")).split(",")
            if e.strip()
        ],
    }


def _supabase_request(method, path, use_service=False, bearer_token=None, params=None, json_data=None, timeout=20, extra_headers=None):
    cfg = _supabase_config()
    base_url = cfg["url"]
    if not base_url:
        raise RuntimeError("Supabase não configurado: defina supabase_url em st.secrets.")

    key = cfg["service_key"] if use_service else cfg["anon_key"]
    if not key:
        segredo = "supabase_service_role_key" if use_service else "supabase_anon_key"
        raise RuntimeError(f"Supabase não configurado: defina {segredo} em st.secrets.")

    headers = {
        "apikey": key,
        "Authorization": f"Bearer {bearer_token or key}",
        "Content-Type": "application/json",
    }
    if extra_headers:
        headers.update(extra_headers)
    resp = requests.request(
        method=method,
        url=f"{base_url}{path}",
        headers=headers,
        params=params,
        json=json_data,
        timeout=timeout,
    )
    if resp.status_code >= 400:
        try:
            detail = resp.json()
        except Exception:
            detail = resp.text
        raise RuntimeError(f"Supabase erro ({resp.status_code}): {detail}")

    if not resp.text.strip():
        return None
    try:
        return resp.json()
    except Exception:
        return resp.text


def _supabase_signup(email, password, full_name):
    return _supabase_request(
        "POST",
        "/auth/v1/signup",
        use_service=False,
        json_data={"email": email, "password": password, "data": {"full_name": full_name}},
    )


def _supabase_signin(email, password):
    return _supabase_request(
        "POST",
        "/auth/v1/token",
        use_service=False,
        params={"grant_type": "password"},
        json_data={"email": email, "password": password},
    )


def _supabase_send_recovery_email(email):
    payload = {"email": email}
    redirect_to = str(st.secrets.get("supabase_recovery_redirect_url", "")).strip()
    if redirect_to:
        payload["redirect_to"] = redirect_to
    return _supabase_request(
        "POST",
        "/auth/v1/recover",
        use_service=False,
        json_data=payload,
    )


def _supabase_generate_recovery_link(email):
    payload = {"type": "recovery", "email": email}
    redirect_to = str(st.secrets.get("supabase_recovery_redirect_url", "")).strip()
    if redirect_to:
        payload["redirect_to"] = redirect_to
    data = _supabase_request(
        "POST",
        "/auth/v1/admin/generate_link",
        use_service=True,
        json_data=payload,
    )
    return data if isinstance(data, dict) else {}


def _supabase_upsert_profile(profile):
    data = _supabase_request(
        "POST",
        "/rest/v1/user_profiles",
        use_service=True,
        params={"on_conflict": "user_id"},
        json_data=profile,
        extra_headers={"Prefer": "resolution=merge-duplicates,return=representation"},
    )
    return data


def _supabase_get_profile(user_id):
    rows = _supabase_request(
        "GET",
        "/rest/v1/user_profiles",
        use_service=True,
        params={"user_id": f"eq.{user_id}", "select": "*", "limit": "1"},
    ) or []
    return rows[0] if rows else None


def _supabase_list_profiles():
    return _supabase_request(
        "GET",
        "/rest/v1/user_profiles",
        use_service=True,
        params={"select": "*", "order": "created_at.desc"},
    ) or []


def _supabase_insert_login_event(evento):
    return _supabase_request(
        "POST",
        "/rest/v1/user_login_events",
        use_service=True,
        json_data=evento,
        extra_headers={"Prefer": "return=minimal"},
    )


def _supabase_list_login_events(limit=200):
    return _supabase_request(
        "GET",
        "/rest/v1/user_login_events",
        use_service=True,
        params={"select": "*", "order": "logged_at.desc", "limit": str(limit)},
    ) or []


def _supabase_admin_users():
    data = _supabase_request(
        "GET",
        "/auth/v1/admin/users",
        use_service=True,
        params={"page": "1", "per_page": "1000"},
    ) or {}
    users = data.get("users", []) if isinstance(data, dict) else []
    return {u.get("id"): u for u in users if u.get("id")}


def _supabase_signout(access_token):
    if not access_token:
        return
    try:
        _supabase_request("POST", "/auth/v1/logout", use_service=False, bearer_token=access_token)
    except Exception:
        pass


def _formatar_erro(msg):
    texto = str(msg)
    texto_lower = texto.lower()
    if "relation" in texto and "does not exist" in texto:
        return "Estrutura de autenticação não encontrada no Supabase. Crie a tabela user_profiles."
    if "user_login_events" in texto and "does not exist" in texto:
        return "Tabela de auditoria não encontrada no Supabase. Execute o SQL atualizado (user_login_events)."
    if "session_duration_seconds" in texto_lower or "logout_reason" in texto_lower or "session_id" in texto_lower:
        return "Estrutura de auditoria desatualizada no Supabase. Reexecute o supabase_auth_schema.sql atualizado."
    if "invalid_credentials" in texto_lower or "invalid login credentials" in texto_lower:
        return "E-mail ou senha inválidos. Se ainda não possui acesso, faça seu cadastro e aguarde aprovação."
    if "email_not_confirmed" in texto_lower:
        return "Seu e-mail ainda não foi confirmado no Supabase."
    if "user already registered" in texto_lower:
        return "Este e-mail já está cadastrado. Tente entrar ou recuperar a senha."
    if "over_email_send_rate_limit" in texto_lower:
        return "Limite de envio de e-mail atingido no Supabase. Aguarde alguns minutos e tente novamente."
    return texto


def _bootstrap_admin_profile(user_id, email, full_name):
    cfg = _supabase_config()
    if email.lower() not in cfg["admin_emails"]:
        return
    _supabase_upsert_profile({
        "user_id": user_id,
        "full_name": full_name or "",
        "role": "admin",
        "status": "active",
        "requested_sectors": _setores_para_storage(SETORES_VALIDOS),
        "allowed_sectors": _setores_para_storage(SETORES_VALIDOS),
    })


def _aplicar_login_sessao(auth_payload):
    auth_data = auth_payload if isinstance(auth_payload, dict) else {}
    user_raw = auth_data.get("user")
    user = user_raw if isinstance(user_raw, dict) else {}
    email = (user.get("email") or "").strip().lower()
    user_id = user.get("id")
    user_meta_raw = user.get("user_metadata")
    user_metadata = user_meta_raw if isinstance(user_meta_raw, dict) else {}
    full_name = user_metadata.get("full_name") or ""

    if not user_id:
        raise RuntimeError("Resposta de login sem usuário.")

    _bootstrap_admin_profile(user_id, email, full_name)
    profile_raw = _supabase_get_profile(user_id)
    profile = profile_raw if isinstance(profile_raw, dict) else None
    if not profile:
        raise RuntimeError("Usuário sem perfil no sistema. Solicite aprovação do administrador.")

    status = (profile.get("status") or "pending").lower()
    if status == "pending":
        raise RuntimeError("Seu cadastro está pendente de aprovação do administrador.")
    if status == "blocked":
        raise RuntimeError("Seu acesso está bloqueado. Procure um administrador.")

    allowed_sectors = _setores_do_storage(profile.get("allowed_sectors"))
    if not allowed_sectors:
        raise RuntimeError("Seu usuário foi aprovado, mas ainda sem setor liberado.")

    active_sector = st.session_state.get("active_sector")
    if active_sector not in allowed_sectors:
        active_sector = allowed_sectors[0]
    st.session_state["active_sector"] = active_sector
    session_started_at = int(time.time())
    session_id = str(uuid.uuid4())
    st.session_state["session_started_at"] = session_started_at
    st.session_state["last_activity_at"] = session_started_at
    st.session_state["session_id"] = session_id

    st.session_state["auth_user"] = {
        "user_id": user_id,
        "email": email,
        "full_name": profile.get("full_name") or full_name or email,
        "role": (profile.get("role") or "user").lower(),
        "status": status,
        "allowed_sectors": allowed_sectors,
        "access_token": auth_data.get("access_token"),
        "session_id": session_id,
    }
    try:
        _supabase_insert_login_event({
            "user_id": user_id,
            "email": email,
            "full_name": profile.get("full_name") or full_name or email,
            "role": (profile.get("role") or "user").lower(),
            "sector_at_login": active_sector,
            "event_type": "login_success",
            "session_id": session_id,
            "session_duration_seconds": 0,
            "logout_reason": "",
        })
    except Exception as e:
        st.session_state["auth_warning"] = _formatar_erro(e)


def _logout(reason="manual"):
    auth_user = st.session_state.get("auth_user")
    auth_user = auth_user if isinstance(auth_user, dict) else {}
    session_started_at = st.session_state.get("session_started_at")
    now_ts = int(time.time())
    duracao = max(0, now_ts - int(session_started_at)) if session_started_at else 0
    if auth_user.get("user_id"):
        try:
            _supabase_insert_login_event({
                "user_id": auth_user.get("user_id"),
                "email": auth_user.get("email", ""),
                "full_name": auth_user.get("full_name", ""),
                "role": auth_user.get("role", "user"),
                "sector_at_login": st.session_state.get("active_sector", ""),
                "event_type": "logout",
                "session_id": auth_user.get("session_id") or st.session_state.get("session_id", ""),
                "session_duration_seconds": duracao,
                "logout_reason": reason,
            })
        except Exception as e:
            st.session_state["auth_warning"] = _formatar_erro(e)

    _supabase_signout(auth_user.get("access_token"))
    for chave in [
        "auth_user", "active_sector", "filtro_mes_ano", "filtro_data", "assinatura_filtros",
        "session_started_at", "last_activity_at", "session_id", "_last_heartbeat_tick"
    ]:
        st.session_state.pop(chave, None)
    st.session_state["intro_exibida"] = False
    st.rerun()


def _render_admin_painel():
    st.subheader("Administração de usuários")
    st.caption("Aprove cadastros e ajuste função/setores a qualquer momento.")

    try:
        profiles = _supabase_list_profiles()
        auth_users = _supabase_admin_users()
    except Exception as e:
        st.error(_formatar_erro(e))
        return

    profiles = [p for p in profiles if isinstance(p, dict)]
    auth_users = auth_users if isinstance(auth_users, dict) else {}
    if not profiles:
        st.info("Ainda não há usuários cadastrados.")
        return

    status_labels = {"pending": "Pendente", "active": "Ativo", "blocked": "Bloqueado"}
    role_options = ["user", "admin"]
    status_options = ["pending", "active", "blocked"]

    for profile in profiles:
        user_id = profile.get("user_id")
        auth_data = auth_users.get(user_id, {})
        auth_data = auth_data if isinstance(auth_data, dict) else {}
        email = auth_data.get("email", "(email não encontrado)")
        user_meta_raw = auth_data.get("user_metadata")
        user_metadata = user_meta_raw if isinstance(user_meta_raw, dict) else {}
        nome = profile.get("full_name") or user_metadata.get("full_name") or "Sem nome"
        role_atual = (profile.get("role") or "user").lower()
        status_atual = (profile.get("status") or "pending").lower()
        setores_liberados = _setores_do_storage(profile.get("allowed_sectors"))
        setores_solicitados = _setores_do_storage(profile.get("requested_sectors"))

        with st.expander(f"{nome} • {email} • {status_labels.get(status_atual, status_atual)}"):
            c1, c2 = st.columns(2)
            with c1:
                novo_role = st.selectbox("Função", role_options, index=role_options.index(role_atual) if role_atual in role_options else 0, key=f"role_{user_id}")
            with c2:
                novo_status = st.selectbox("Status", status_options, index=status_options.index(status_atual) if status_atual in status_options else 0, key=f"status_{user_id}")

            st.caption(f"Setores solicitados: {', '.join(_setor_label(s) for s in setores_solicitados) or 'Nenhum'}")
            novos_setores = st.multiselect(
                "Setores liberados",
                options=SETORES_VALIDOS,
                default=setores_liberados,
                format_func=_setor_label,
                key=f"setores_{user_id}",
            )

            c3, c4 = st.columns(2)
            with c3:
                if st.button("Enviar reset por e-mail", key=f"reset_email_{user_id}"):
                    try:
                        _supabase_send_recovery_email(str(email).strip().lower())
                        st.success("Solicitação de recuperação enviada.")
                    except Exception as e:
                        st.error(_formatar_erro(e))
            with c4:
                if st.button("Gerar link de reset", key=f"reset_link_{user_id}"):
                    try:
                        data_link = _supabase_generate_recovery_link(str(email).strip().lower())
                        action_link = data_link.get("action_link")
                        if not action_link and isinstance(data_link.get("properties"), dict):
                            action_link = data_link["properties"].get("action_link")
                        if action_link:
                            st.session_state[f"recovery_link_{user_id}"] = action_link
                            st.success("Link de recuperação gerado.")
                        else:
                            st.warning("Não foi possível obter o link na resposta do Supabase.")
                    except Exception as e:
                        st.error(_formatar_erro(e))

            link_memoria = st.session_state.get(f"recovery_link_{user_id}")
            if link_memoria:
                st.caption("Link de recuperação (uso administrativo):")
                st.code(link_memoria)

            if st.button("Salvar usuário", key=f"save_{user_id}"):
                try:
                    _supabase_upsert_profile({
                        "user_id": user_id,
                        "full_name": profile.get("full_name") or nome,
                        "role": novo_role,
                        "status": novo_status,
                        "requested_sectors": profile.get("requested_sectors") or _setores_para_storage(setores_solicitados),
                        "allowed_sectors": _setores_para_storage(novos_setores),
                    })
                    st.success("Usuário atualizado.")
                    st.rerun()
                except Exception as e:
                    st.error(_formatar_erro(e))

    st.markdown("---")
    st.subheader("Logs de acesso")
    try:
        eventos = _supabase_list_login_events(limit=300)
    except Exception as e:
        st.error(_formatar_erro(e))
        return

    eventos = [e for e in eventos if isinstance(e, dict)]
    if not eventos:
        st.info("Sem registros de login até o momento.")
        return

    df_logs = pd.DataFrame(eventos)
    if "logged_at" in df_logs.columns:
        dt = pd.to_datetime(df_logs["logged_at"], errors="coerce", utc=True).dt.tz_convert("America/Sao_Paulo")
        df_logs["Data/Hora"] = dt.dt.strftime("%d/%m/%Y %H:%M:%S")
    if "session_duration_seconds" in df_logs.columns:
        df_logs["Duração sessão"] = df_logs["session_duration_seconds"].apply(_formatar_duracao_segundos)
    if "logout_reason" in df_logs.columns:
        mapa_reason = {"manual": "Logout manual", "inactivity": "Inatividade"}
        df_logs["Motivo logout"] = df_logs["logout_reason"].map(mapa_reason).fillna(df_logs["logout_reason"])
    colunas = [c for c in ["Data/Hora", "full_name", "email", "role", "sector_at_login", "event_type", "Duração sessão", "Motivo logout"] if c in df_logs.columns]
    st.dataframe(df_logs[colunas], use_container_width=True, height=320)

# --- Autenticação ---
def tela_login():
    _render_logo_tema(LOGO_FULL_LIGHT_PATH, LOGO_FULL_DARK_PATH, max_width=440)
    st.title("Acesso ao MAGO")
    st.text("Monitoramento e Acompanhamento de Gestão Operacional")
    st.caption("Faça login ou Cadastre-se (necessário aprovação de um admin)")

    tab_login, tab_cadastro = st.tabs(["Entrar", "Cadastrar"])

    with tab_login:
        with st.form("form_login", clear_on_submit=False):
            email = st.text_input("E-mail", key="login_email").strip().lower()
            senha = st.text_input("Senha", type="password", key="login_senha")
            entrar = st.form_submit_button("Entrar")
        if entrar:
            try:
                auth_payload = _supabase_signin(email=email, password=senha)
                _aplicar_login_sessao(auth_payload)
                st.rerun()
            except Exception as e:
                st.error(_formatar_erro(e))

        with st.expander("Esqueci minha senha"):
            email_rec = st.text_input("E-mail para recuperação", key="recover_email").strip().lower()
            if st.button("Enviar link de recuperação", key="btn_recover_self"):
                if not email_rec:
                    st.error("Informe o e-mail para recuperação.")
                else:
                    try:
                        _supabase_send_recovery_email(email_rec)
                        st.success("Se o e-mail estiver cadastrado, o link de recuperação foi enviado.")
                    except Exception as e:
                        st.error(_formatar_erro(e))

    with tab_cadastro:
        with st.form("form_cadastro", clear_on_submit=True):
            nome = st.text_input("Nome completo", key="cad_nome").strip()
            email_cad = st.text_input("E-mail", key="cad_email").strip().lower()
            senha_cad = st.text_input("Senha", type="password", key="cad_senha")
            senha_conf = st.text_input("Confirmar senha", type="password", key="cad_senha_conf")
            setores_req = st.multiselect("Setor(es) solicitado(s)", SETORES_VALIDOS, default=["SOC"], format_func=_setor_label, key="cad_setores")
            cadastrar = st.form_submit_button("Solicitar cadastro")

        if cadastrar:
            if not nome or not email_cad or not senha_cad:
                st.error("Preencha nome, e-mail e senha.")
            elif senha_cad != senha_conf:
                st.error("As senhas não conferem.")
            elif len(senha_cad) < 8:
                st.error("A senha deve ter ao menos 8 caracteres.")
            else:
                try:
                    signup = _supabase_signup(email=email_cad, password=senha_cad, full_name=nome)
                    signup_data = signup if isinstance(signup, dict) else {}
                    user_raw = signup_data.get("user")
                    user = user_raw if isinstance(user_raw, dict) else {}
                    user_id = user.get("id")
                    if not user_id:
                        raise RuntimeError("Não foi possível criar o usuário no Supabase.")

                    _supabase_upsert_profile({
                        "user_id": user_id,
                        "full_name": nome,
                        "role": "user",
                        "status": "pending",
                        "requested_sectors": _setores_para_storage(setores_req),
                        "allowed_sectors": "",
                    })
                    st.success("Cadastro recebido. Aguarde aprovação do administrador.")
                except Exception as e:
                    st.error(_formatar_erro(e))


if "auth_user" not in st.session_state:
    if not st.session_state.get("intro_exibida"):
        if _render_intro_tela_cheia():
            time.sleep(3.2)
        st.session_state["intro_exibida"] = True
        st.rerun()
    tela_login()
    st.stop()

loading_overlay_slot = None
if st.session_state.pop("exibir_loading_filtros", False):
    loading_overlay_slot = st.empty()
    _render_loading_animado(container=loading_overlay_slot)
    time.sleep(1.1)

main_logo_slot = st.empty()
_render_logo_tema(LOGO_FULL_LIGHT_PATH, LOGO_FULL_DARK_PATH, max_width=460, container=main_logo_slot)
st.caption("Monitoramento e Análise de Gestão Operacional")
if st.session_state.get("auth_warning"):
    st.warning(st.session_state.pop("auth_warning"))

sidebar_logo_slot = st.sidebar.empty()
_render_sidebar_icon(sidebar_logo_slot)
_render_icono_sidebar_recolhida()
auth_user = st.session_state.get("auth_user", {})
auth_user = auth_user if isinstance(auth_user, dict) else {}

idle_timeout_min = int(st.secrets.get("auth_idle_timeout_minutes", 30))
idle_timeout_sec = max(60, idle_timeout_min * 60)
heartbeat_sec = int(st.secrets.get("auth_heartbeat_seconds", 30))
heartbeat_sec = min(max(heartbeat_sec, 10), 300)

tick = st_autorefresh(interval=heartbeat_sec * 1000, key="auth_session_heartbeat")
last_tick = st.session_state.get("_last_heartbeat_tick")
is_heartbeat = last_tick is not None and tick != last_tick
st.session_state["_last_heartbeat_tick"] = tick

agora = int(time.time())
if "session_started_at" not in st.session_state:
    st.session_state["session_started_at"] = agora
if "last_activity_at" not in st.session_state:
    st.session_state["last_activity_at"] = agora

if not is_heartbeat:
    st.session_state["last_activity_at"] = agora

tempo_logado_seg = max(0, agora - int(st.session_state.get("session_started_at", agora)))
tempo_inativo_seg = max(0, agora - int(st.session_state.get("last_activity_at", agora)))
if tempo_inativo_seg >= idle_timeout_sec:
    _logout("inactivity")

st.sidebar.caption(f"Usuário: {auth_user.get('full_name', '')}")
st.sidebar.caption(f"Perfil: {auth_user.get('role', 'user').upper()}")
with st.sidebar:
    _render_tempo_logado_realtime(st.session_state.get("session_started_at", agora))



setores_liberados = auth_user.get("allowed_sectors", [])
if not isinstance(setores_liberados, list):
    setores_liberados = _setores_do_storage(setores_liberados)
if setores_liberados:
    setor_ativo = st.sidebar.selectbox(
        "Setor ativo",
        options=setores_liberados,
        format_func=_setor_label,
        key="active_sector",
    )
else:
    setor_ativo = None

area_options = ["Mapa"]
if auth_user.get("role") == "admin":
    area_options.append("Administração")
area_escolhida = st.sidebar.radio("Área", area_options, index=0)

if st.sidebar.button("Sair"):
    _logout("manual")


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
    col_endereco = _selecionar_coluna(
        df_full,
        ["Endereço", "Endereco", "Logradouro", "Endereço da atividade", "Endereco da atividade", "Endereço do cliente", "Endereco do cliente"]
    ) or _selecionar_coluna_fuzzy(df_full, inclui=["endere"]) or _selecionar_coluna_fuzzy(df_full, inclui=["logradouro"])
    df["Endereço"] = df_full[col_endereco] if col_endereco else ""
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
    coordenadas_values = worksheets["coordenadas"].get_all_values() if "coordenadas" in worksheets else []

    df_dados = _valores_para_df(dados_values)
    df_coordenadas = _padronizar_coordenadas(_valores_para_df(coordenadas_values))
    return df_dados, df_coordenadas


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
    s = serie.astype(str).str.strip()
    data_dmy = pd.to_datetime(s, dayfirst=True, errors="coerce")

    faltantes = data_dmy.isna()
    if faltantes.any():
        data_ymd = pd.to_datetime(s[faltantes], dayfirst=False, errors="coerce")
        data_dmy.loc[faltantes] = data_ymd

    faltantes = data_dmy.isna()
    if faltantes.any():
        data_generica = pd.to_datetime(s[faltantes], errors="coerce")
        data_dmy.loc[faltantes] = data_generica

    faltantes = data_dmy.isna()
    if faltantes.any():
        extrair_data = s[faltantes].str.extract(r"(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{2,4})", expand=False)
        data_extraida = pd.to_datetime(extrair_data, dayfirst=True, errors="coerce")
        data_dmy.loc[faltantes] = data_extraida

    return data_dmy

def _carregar_rastro_csv(uploaded_file):
    df_raw = None
    for encoding in ("utf-8-sig", "utf-8", "cp1252", "latin-1"):
        try:
            uploaded_file.seek(0)
            df_raw = pd.read_csv(uploaded_file, sep=";", dtype=str, encoding=encoding)
            break
        except Exception:
            continue

    if df_raw is None:
        return pd.DataFrame(columns=["DataHora", "Data_BR", "Latitude", "Longitude", "Veiculo"])

    col_lat = _selecionar_coluna(df_raw, ["Latitude"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["lat"])
    col_lon = _selecionar_coluna(df_raw, ["Longitude"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["lon"])
    col_data = _selecionar_coluna(df_raw, ["Data_Captura", "Data Captura", "Data"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["data"])
    col_veiculo = _selecionar_coluna(df_raw, ["Veiculo", "Veículo", "Placa"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["veiculo"]) or _selecionar_coluna_fuzzy(df_raw, inclui=["placa"])

    if not col_lat or not col_lon or not col_data:
        return pd.DataFrame(columns=["DataHora", "Data_BR", "Latitude", "Longitude", "Veiculo"])

    df = pd.DataFrame()
    df["Latitude"] = pd.to_numeric(df_raw[col_lat].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    df["Longitude"] = pd.to_numeric(df_raw[col_lon].astype(str).str.replace(",", ".", regex=False), errors="coerce")
    df["Veiculo"] = df_raw[col_veiculo].astype(str).str.strip() if col_veiculo else ""
    data_texto = df_raw[col_data].astype(str).str.replace(" - ", " ", regex=False).str.strip()
    df["DataHora"] = pd.to_datetime(data_texto, dayfirst=True, errors="coerce")
    df["Data_BR"] = df["DataHora"].dt.strftime("%d/%m/%Y")

    df = df.dropna(subset=["Latitude", "Longitude", "DataHora"]).sort_values("DataHora")
    return df

def _reduzir_pontos_trajeto_df(df_trajeto, limite=1500):
    if df_trajeto.empty or len(df_trajeto) <= limite:
        return df_trajeto
    passo = max(1, len(df_trajeto) // limite)
    df_reduzido = df_trajeto.iloc[::passo].copy()
    if df_reduzido.index[-1] != df_trajeto.index[-1]:
        df_reduzido = pd.concat([df_reduzido, df_trajeto.iloc[[-1]]])
    return df_reduzido

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


def _gerar_designados_fim_jornada(df_execucao):
    if df_execucao.empty:
        return pd.DataFrame(columns=_colunas_padrao_designados())

    col_causa = _selecionar_coluna(
        df_execucao,
        ["Causa/Descritivo Resultado", "Causa", "Descritivo"]
    ) or _selecionar_coluna_fuzzy(df_execucao, inclui=["causa"]) or _selecionar_coluna_fuzzy(df_execucao, inclui=["descritivo"])

    if not col_causa:
        return pd.DataFrame(columns=_colunas_padrao_designados())

    causa_alvo = "fjl - fim da jornada laborativa"
    serie_causa = df_execucao[col_causa].astype(str).str.strip().str.casefold()
    base = df_execucao[serie_causa == causa_alvo].copy()
    if base.empty:
        return pd.DataFrame(columns=_colunas_padrao_designados())

    col_id = _selecionar_coluna(base, ["Código TdC", "codigo_tdc", "codigo tdc"]) or _selecionar_coluna_fuzzy(base, inclui=["codigo", "tdc"])
    col_cliente = _selecionar_coluna(base, ["Código Cliente", "Codigo Cliente", "Cliente ID", "Instalação", "Instalacao"]) or _selecionar_coluna_fuzzy(base, inclui=["codigo", "cliente"])
    col_equipe = _selecionar_coluna(base, ["Equipe", "Equipe Designada", "Recurso"]) or _selecionar_coluna_fuzzy(base, inclui=["equipe"])
    col_tipo = _selecionar_coluna(base, ["Ciclo de trabalho", "Ciclo Trabalho", "Tipo TdC", "Tipo Serviço", "Setor"]) or _selecionar_coluna_fuzzy(base, inclui=["ciclo"]) or _selecionar_coluna_fuzzy(base, inclui=["tipo"])
    col_estado = _selecionar_coluna(base, ["Estado TdC", "Estado", "Resultado"]) or _selecionar_coluna_fuzzy(base, inclui=["estado"])
    col_data = _selecionar_coluna(base, ["Data Início", "Data Inicio", "Data"]) or _selecionar_coluna_fuzzy(base, inclui=["data"])
    col_endereco = _selecionar_coluna(base, ["Endereço", "Endereco", "Logradouro"]) or _selecionar_coluna_fuzzy(base, inclui=["endere"]) or _selecionar_coluna_fuzzy(base, inclui=["logradouro"])
    col_lat = _selecionar_coluna(base, ["Latitude", "lat"]) or _selecionar_coluna_fuzzy(base, inclui=["lat"])
    col_lon = _selecionar_coluna(base, ["Longitude", "lon", "long"]) or _selecionar_coluna_fuzzy(base, inclui=["lon"]) or _selecionar_coluna_fuzzy(base, inclui=["long"])

    df = pd.DataFrame()
    df["Código TdC"] = base[col_id] if col_id else ""
    df["Código Cliente"] = base[col_cliente] if col_cliente else ""
    df["Equipe Designada"] = base[col_equipe] if col_equipe else ""
    df["Tipo Serviço"] = base[col_tipo] if col_tipo else ""
    df["Estado"] = base[col_estado] if col_estado else ""
    df["Data"] = base[col_data] if col_data else ""
    df["Endereço"] = base[col_endereco] if col_endereco else ""
    df["Latitude"] = pd.to_numeric(base[col_lat], errors="coerce") if col_lat else pd.NA
    df["Longitude"] = pd.to_numeric(base[col_lon], errors="coerce") if col_lon else pd.NA
    return df

def _mascara_fim_jornada(df_execucao):
    if df_execucao.empty:
        return pd.Series(False, index=df_execucao.index)
    col_causa = _selecionar_coluna(
        df_execucao,
        ["Causa/Descritivo Resultado", "Causa", "Descritivo"]
    ) or _selecionar_coluna_fuzzy(df_execucao, inclui=["causa"]) or _selecionar_coluna_fuzzy(df_execucao, inclui=["descritivo"])
    if not col_causa:
        return pd.Series(False, index=df_execucao.index)
    return df_execucao[col_causa].astype(str).str.strip().str.casefold().eq("fjl - fim da jornada laborativa")

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
        df, df_coordenadas = _carregar_gsheet()
    else:
        df = _carregar_local()
        df_coordenadas = _carregar_coordenadas_local()
    df = _aplicar_tramites(df)
    mascara_fjl = _mascara_fim_jornada(df)
    df_designados = _gerar_designados_fim_jornada(df)
    df_execucao = df.loc[~mascara_fjl].copy() if mascara_fjl.any() else df
    return df_execucao, df_designados, df_coordenadas


if area_escolhida == "Administração":
    _render_admin_painel()
    st.stop()

if not setor_ativo:
    st.error("Seu usuário não possui setor liberado.")
    st.stop()

if setor_ativo != "SOC":
    _render_logo_tema(LOGO_LIGHT_PATH, LOGO_DARK_PATH, max_width=220, container=main_logo_slot)
    st.info(f"O módulo do setor **{_setor_label(setor_ativo)}** está em desenvolvimento. Em breve.")
    st.stop()

try:
    df, df_designados, df_coordenadas = carregar_dados()

    COL_ID = _selecionar_coluna(df, ["Código TdC", "codigo tdc", "codigo_tdc"]) or "Código TdC"
    COL_EQUIPE = _selecionar_coluna(df, ["Equipe", "Equipe_x"]) or "Equipe"
    COL_LAT = _selecionar_coluna(df, ["Latitude", "lat"]) or "Latitude"
    COL_LON = _selecionar_coluna(df, ["Longitude", "lon", "long"]) or "Longitude"
    COL_DATA = _selecionar_coluna(df, ["Data Início", "Data Inicio", "Data"]) or "Data Início"
    COL_HORA_INI = COL_DATA
    COL_HORA_FIM = _selecionar_coluna(df, ["Data Fim", "Data Final"]) or COL_DATA
    COL_STATUS = _selecionar_coluna(df, ["Estado TdC", "Estado", "Resultado"]) or "Resultado"
    COL_RETORNO = _selecionar_coluna(df, ["Resultado", "Retorno"]) or COL_STATUS
    COL_SETOR = "Tipo TdC"
    COL_TRAMITE = _selecionar_coluna(df, ["Tramite", "Trâmite"]) or "Tramite"
    COL_CAUSA = _selecionar_coluna(df, ["Causa/Descritivo Resultado", "Causa", "Descritivo"]) or "Causa/Descritivo Resultado"
    COL_D_ID = 'Código TdC'
    COL_D_CLIENTE = 'Código Cliente'
    COL_D_EQUIPE = 'Equipe Designada'
    COL_D_TIPO = 'Tipo Serviço'
    COL_D_ESTADO = 'Estado'
    COL_D_DATA = 'Data'
    COL_D_ENDERECO = 'Endereço'
    COL_D_LAT = 'Latitude'
    COL_D_LON = 'Longitude'

    cols_criticas = [COL_ID, COL_EQUIPE, COL_LAT, COL_LON, COL_DATA, COL_SETOR, COL_STATUS, COL_RETORNO]
    faltantes = [c for c in cols_criticas if c not in df.columns]
    if faltantes:
        st.error(f"A base de execução está sem colunas obrigatórias: {', '.join(faltantes)}")
        st.stop()

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
    if not meses_disponiveis:
        st.warning("Não foi possível montar o filtro de mês. Verifique o formato das colunas de data.")
        st.stop()
    nomes_meses = {
        "01": "janeiro",
        "02": "fevereiro",
        "03": "março",
        "04": "abril",
        "05": "maio",
        "06": "junho",
        "07": "julho",
        "08": "agosto",
        "09": "setembro",
        "10": "outubro",
        "11": "novembro",
        "12": "dezembro",
    }
    meses_labels = [f"{nomes_meses.get(m.split('-')[1], m.split('-')[1])}/{m.split('-')[0]}" for m in meses_disponiveis]
    mes_map = dict(zip(meses_labels, meses_disponiveis))
    if "filtro_mes_ano" not in st.session_state or st.session_state["filtro_mes_ano"] not in meses_labels:
        st.session_state["filtro_mes_ano"] = meses_labels[0]
    mes_selecionado_label = st.sidebar.selectbox("🗓️ Mês/Ano", meses_labels, key="filtro_mes_ano")
    mes_selecionado = mes_map[mes_selecionado_label]

    df_mes = df[df["Mes"] == mes_selecionado]
    df_designados_mes = df_designados[df_designados["Mes"] == mes_selecionado]

    datas_ordenadas = sorted(
        set(df_mes.dropna(subset=["Data_BR"])["Data_BR"].tolist() + df_designados_mes.dropna(subset=["Data_BR"])["Data_BR"].tolist()),
        key=lambda x: pd.to_datetime(x, dayfirst=True, errors="coerce")
    )
    if not datas_ordenadas:
        st.warning("Não foi possível montar o filtro de data para o mês selecionado.")
        st.stop()
    if "filtro_data" not in st.session_state or st.session_state["filtro_data"] not in datas_ordenadas:
        st.session_state["filtro_data"] = datas_ordenadas[0]
    data_selecionada = st.sidebar.selectbox("📅 Selecione a Data", datas_ordenadas, key="filtro_data")

    df_f1 = df_mes[df_mes["Data_BR"] == data_selecionada]
    df_designados_f1 = df_designados_mes[df_designados_mes["Data_BR"] == data_selecionada]

    st.sidebar.markdown("---")

    equipes_disponiveis = sorted(df_f1[COL_EQUIPE].dropna().unique().tolist())
    todas_equipes = st.sidebar.checkbox("Selecionar todas as Equipes", value=False)
    if todas_equipes:
        equipes_selecionadas = equipes_disponiveis
    else:
        equipes_selecionadas = st.sidebar.multiselect("👷 Equipes", equipes_disponiveis)

    df_f2 = df_f1[df_f1[COL_EQUIPE].isin(equipes_selecionadas)]

    setores_disponiveis = sorted(df_f2[COL_SETOR].dropna().unique().tolist())
    todos_setores = st.sidebar.checkbox("Selecionar todos os Setores", value=False)
    if todos_setores:
        setores_selecionados = setores_disponiveis
    else:
        setores_selecionados = st.sidebar.multiselect("🏢 Setores ", setores_disponiveis)

    df_f3 = df_f2[df_f2[COL_SETOR].isin(setores_selecionados)]

    status_disponiveis = sorted(df_f3[COL_STATUS].dropna().unique().tolist())
    todos_status = st.sidebar.checkbox("Selecionar todos os Status", value=True)
    if todos_status:
        status_selecionados = status_disponiveis
    else:
        status_selecionados = st.sidebar.multiselect("✅ Status da Atividade", status_disponiveis)

    filtros_aplicados = bool(
        setores_selecionados
        or equipes_selecionadas
        or (not todos_status and status_selecionados)
    )

    assinatura_filtros = (
        mes_selecionado,
        data_selecionada,
        tuple(equipes_selecionadas),
        tuple(setores_selecionados),
        bool(todos_status),
        tuple(status_selecionados),
    )
    assinatura_anterior = st.session_state.get("assinatura_filtros")
    if assinatura_anterior is None:
        st.session_state["assinatura_filtros"] = assinatura_filtros
    elif assinatura_anterior != assinatura_filtros:
        st.session_state["assinatura_filtros"] = assinatura_filtros
        st.session_state["exibir_loading_filtros"] = True
        st.rerun()

    df_filtrado = df_f3[df_f3[COL_STATUS].isin(status_selecionados)]

    df_filtrado = df_filtrado.dropna(subset=[COL_LAT, COL_LON])
    df_filtrado = df_filtrado.sort_values(by=[COL_EQUIPE, "DataHora"])

    st.sidebar.markdown("---")
    st.sidebar.subheader("🚗 Rastro do veículo")
    rastros_processados = []
    exibir_rastro_veiculo = False
    total_rastro_pontos = 0
    total_rastro_arquivos = 0
    if equipes_selecionadas:
        arquivos_rastro = st.sidebar.file_uploader(
            "Importar arquivos(.csv) de rastreamento veicular do GPM",
            type=["csv"],
            accept_multiple_files=True,
            key="upload_rastro_csv",
            help="A opção aparece após selecionar equipe(s). Você pode importar múltiplos arquivos.",
        )
        if arquivos_rastro:
            exibir_rastro_veiculo = st.sidebar.checkbox("Exibir rastro real do veículo", value=True)
            equipes_norm_map = {_normalizar_texto_filtro(eq): eq for eq in equipes_selecionadas}

            for i, arquivo in enumerate(arquivos_rastro):
                nome_norm = _normalizar_texto_filtro(arquivo.name)
                equipe_default = equipes_selecionadas[0]
                for chave, equipe_nome in equipes_norm_map.items():
                    if chave and chave in nome_norm:
                        equipe_default = equipe_nome
                        break
                idx_default = equipes_selecionadas.index(equipe_default) if equipe_default in equipes_selecionadas else 0
                equipe_arquivo = st.sidebar.selectbox(
                    f"Equipe do arquivo {i + 1}: {arquivo.name}",
                    options=equipes_selecionadas,
                    index=idx_default,
                    key=f"rastro_equipe_{i}",
                )

                df_rastro = _carregar_rastro_csv(arquivo)
                df_rastro = df_rastro[df_rastro["Data_BR"] == data_selecionada]
                if not df_rastro.empty:
                    rastros_processados.append({"arquivo": arquivo.name, "equipe": equipe_arquivo, "df": df_rastro})
                    total_rastro_pontos += len(df_rastro)
            total_rastro_arquivos = len(rastros_processados)

    st.sidebar.markdown("---")
    st.sidebar.subheader("Designados")
    exibir_designados = st.sidebar.checkbox("Exibir camada de designados", value=True)

    # Referência de execução para identificar "sobra":
    # mesma data e mesmas equipes selecionadas (independente de setor/status).
    df_execucao_referencia = df_f1[df_f1[COL_EQUIPE].isin(equipes_selecionadas)]
    codigos_executados = {
        _normalizar_chave_codigo(cod)
        for cod in df_execucao_referencia[COL_ID].tolist()
        if _normalizar_chave_codigo(cod)
    }

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
        ].drop(columns=["_equipe_norm"], errors="ignore")
    else:
        df_designados_filtrado = df_designados_tmp.iloc[0:0].drop(columns=["_equipe_norm"], errors="ignore")

    if codigos_executados and not df_designados_filtrado.empty:
        df_designados_filtrado["_codigo_norm"] = df_designados_filtrado[COL_D_ID].apply(_normalizar_chave_codigo)
        df_designados_filtrado = df_designados_filtrado[
            ~df_designados_filtrado["_codigo_norm"].isin(codigos_executados)
        ].drop(columns=["_codigo_norm"], errors="ignore")

    designados_com_coord = 0
    if exibir_designados and not df_designados_filtrado.empty:
        designados_com_coord = int(df_designados_filtrado[[COL_D_LAT, COL_D_LON]].notna().all(axis=1).sum())
        df_designados_filtrado = df_designados_filtrado.dropna(subset=[COL_D_LAT, COL_D_LON])
    total_designados_filtrados = len(df_designados_filtrado)

    tem_rastro_visivel = exibir_rastro_veiculo and total_rastro_arquivos > 0
    if df_filtrado.empty and (not exibir_designados or df_designados_filtrado.empty) and not tem_rastro_visivel:
        _render_logo_tema(LOGO_FULL_LIGHT_PATH, LOGO_FULL_DARK_PATH, max_width=460, container=main_logo_slot)
        st.warning("Nenhum dado encontrado com os filtros selecionados.")
    else:
        if filtros_aplicados:
            _render_logo_tema(LOGO_LIGHT_PATH, LOGO_DARK_PATH, max_width=180, container=main_logo_slot)
        else:
            _render_logo_tema(LOGO_FULL_LIGHT_PATH, LOGO_FULL_DARK_PATH, max_width=460, container=main_logo_slot)
        latitudes = []
        longitudes = []
        if not df_filtrado.empty:
            latitudes.extend(df_filtrado[COL_LAT].tolist())
            longitudes.extend(df_filtrado[COL_LON].tolist())
        if exibir_designados and not df_designados_filtrado.empty:
            latitudes.extend(df_designados_filtrado[COL_D_LAT].tolist())
            longitudes.extend(df_designados_filtrado[COL_D_LON].tolist())
        if tem_rastro_visivel:
            for rastro in rastros_processados:
                latitudes.extend(rastro["df"]["Latitude"].tolist())
                longitudes.extend(rastro["df"]["Longitude"].tolist())

        centro_lat = sum(latitudes) / len(latitudes)
        centro_lon = sum(longitudes) / len(longitudes)
        mapa = folium.Map(location=[centro_lat, centro_lon], zoom_start=13)
        camada_exec = folium.FeatureGroup(name="✅ Serviços executados", show=True)
        camada_designados = folium.FeatureGroup(name="🗂️ Serviços designados", show=True)
        camada_rastro = folium.FeatureGroup(name="🚗 Rastro real do veículo", show=True)

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

        if tem_rastro_visivel:
            for index, rastro in enumerate(rastros_processados):
                dados_rastro = rastro["df"]
                nome_equipe = rastro["equipe"]
                nome_arquivo = rastro["arquivo"]
                cor_rastro = cores_equipe[(index + 2) % len(cores_equipe)]
                placa_rastro = str(dados_rastro["Veiculo"].dropna().iloc[0]).strip() if "Veiculo" in dados_rastro.columns and not dados_rastro["Veiculo"].dropna().empty else nome_equipe

                dados_rastro_plot = _reduzir_pontos_trajeto_df(dados_rastro, limite=900)
                coordenadas_rastro = dados_rastro_plot[["Latitude", "Longitude"]].values.tolist()
                if len(coordenadas_rastro) >= 2:
                    for i in range(len(dados_rastro_plot) - 1):
                        ponto_a = dados_rastro_plot.iloc[i]
                        ponto_b = dados_rastro_plot.iloc[i + 1]
                        hora_a = ponto_a["DataHora"].strftime("%d/%m/%Y %H:%M:%S")
                        hora_b = ponto_b["DataHora"].strftime("%d/%m/%Y %H:%M:%S")
                        folium.PolyLine(
                            [[ponto_a["Latitude"], ponto_a["Longitude"]], [ponto_b["Latitude"], ponto_b["Longitude"]]],
                            color=cor_rastro,
                            weight=3,
                            opacity=0.9,
                            dash_array="8,6",
                            tooltip=f"{placa_rastro} | {hora_a} → {hora_b}",
                        ).add_to(camada_rastro)

                for _, ponto in dados_rastro_plot.iterrows():
                    datahora_txt = ponto["DataHora"].strftime("%d/%m/%Y %H:%M:%S")
                    folium.CircleMarker(
                        location=[ponto["Latitude"], ponto["Longitude"]],
                        radius=4,
                        color="#b04a00",
                        fill=True,
                        fill_color="#ff8c00",
                        fill_opacity=1,
                        weight=2,
                        tooltip=f"{placa_rastro} | {datahora_txt}",
                        popup=f"{placa_rastro}<br>{datahora_txt}"
                    ).add_to(camada_rastro)

                if not dados_rastro_plot.empty:
                    inicio = dados_rastro_plot.iloc[0]
                    fim = dados_rastro_plot.iloc[-1]
                    inicio_txt = inicio["DataHora"].strftime("%d/%m/%Y %H:%M:%S")
                    fim_txt = fim["DataHora"].strftime("%d/%m/%Y %H:%M:%S")
                    folium.Marker(
                        location=[inicio["Latitude"], inicio["Longitude"]],
                        tooltip=f"🚙 Início rastro | {placa_rastro} | {inicio_txt}",
                        popup=f"Início rastro<br>{placa_rastro}<br>{inicio_txt}",
                        icon=folium.Icon(color="blue", icon="play")
                    ).add_to(camada_rastro)
                    folium.Marker(
                        location=[fim["Latitude"], fim["Longitude"]],
                        tooltip=f"🛑 Fim rastro | {placa_rastro} | {fim_txt}",
                        popup=f"Fim rastro<br>{placa_rastro}<br>{fim_txt}",
                        icon=folium.Icon(color="blue", icon="stop")
                    ).add_to(camada_rastro)

        camada_exec.add_to(mapa)
        if exibir_designados:
            camada_designados.add_to(mapa)
        if tem_rastro_visivel:
            camada_rastro.add_to(mapa)
        folium.LayerControl(collapsed=True).add_to(mapa)

        st.markdown("""
        **Legenda do Mapa:** \n
        🟢  Fundo Verde: Realizado | 🔴 Fundo Vermelho: Não Realizado | ⚫ Fundo Cinza: Designado |  
        🟩 Pino Verde: Início da Rota | ⬛ Pino Preto: Fim da Rota | 🔶 Linha tracejada: Rastro do veículo
        """)
        # Apenas para debug (descomentar para visualizar)
        if exibir_designados:
            st.caption(f"Designados filtrados: {total_designados_filtrados} | Com coordenadas: {designados_com_coord}")
        if tem_rastro_visivel:
            st.caption(f"Rastros carregados: {total_rastro_arquivos} arquivo(s) | Pontos: {total_rastro_pontos}")

        def _resumo_lista(lista, limite=3):
            itens = [str(x).strip() for x in lista if str(x).strip()]
            if not itens:
                return "Nenhum"
            if len(itens) <= limite:
                return ", ".join(itens)
            return f"{', '.join(itens[:limite])} (+{len(itens) - limite})"

        equipes_txt = html_lib.escape(_resumo_lista(equipes_selecionadas), quote=True)
        setores_txt = html_lib.escape(_resumo_lista(setores_selecionados), quote=True)
        status_txt = html_lib.escape(_resumo_lista(status_selecionados), quote=True)
        mes_txt = html_lib.escape(str(mes_selecionado_label), quote=True)
        data_txt = html_lib.escape(str(data_selecionada), quote=True)
        qtd_exec_txt = html_lib.escape(str(len(df_filtrado)), quote=True)
        qtd_visitas_total = len(df_f3)
        qtd_total_servicos = total_designados_filtrados + qtd_visitas_total
        qtd_total_servicos_txt = html_lib.escape(str(qtd_total_servicos), quote=True)
        qtd_des_txt = html_lib.escape(str(total_designados_filtrados), quote=True)
        qtd_rastro_arquivos_txt = html_lib.escape(str(total_rastro_arquivos), quote=True)
        qtd_rastro_pontos_txt = html_lib.escape(str(total_rastro_pontos), quote=True)

        resumo_filtros_html = f"""
        <div style="
            position: fixed;
            top: 10px;
            left: 50px;
            z-index: 9999;
            background: rgba(255,255,255,0.65);
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 8px;
            width: 320px;
            font-size: 11px;
            font-family: Arial, sans-serif;
            box-shadow: 0 1px 6px rgba(0,0,0,0.2);
        ">
            <div style="display:flex; align-items:center; justify-content:space-between; margin-bottom:6px;">
                <div style="font-weight: bold;">Resumo dos filtros</div>
                <button id="resumo-filtros-btn"
                        onclick="var c=document.getElementById('resumo-filtros-conteudo');var b=document.getElementById('resumo-filtros-btn');c.style.display=(c.style.display==='none')?'block':'none';b.innerText=(c.style.display==='none')?'Mostrar':'Ocultar';"
                        style="font-size:10px; padding:2px 6px; border:1px solid #bbb; border-radius:4px; background:#fff; cursor:pointer;">
                    Recolher
                </button>
            </div>
            <div id="resumo-filtros-conteudo">
            <table style="width:100%; border-collapse: collapse;">
                <tr><td style="font-weight:bold; padding:2px 4px;">Mês/Ano</td><td style="padding:2px 4px;">{mes_txt}</td></tr>
                <tr><td style="font-weight:bold; padding:2px 4px;">Data</td><td style="padding:2px 4px;">{data_txt}</td></tr>
                <tr><td style="font-weight:bold; padding:2px 4px;">Equipes</td><td style="padding:2px 4px;">{equipes_txt}</td></tr>
                <tr><td style="font-weight:bold; padding:2px 4px;">Setores</td><td style="padding:2px 4px;">{setores_txt}</td></tr>
                <tr><td style="font-weight:bold; padding:2px 4px;">Status</td><td style="padding:2px 4px;">{status_txt}</td></tr>
                <tr><td style="font-weight:bold; padding:2px 4px;">Serv. Finalizados</td><td style="padding:2px 4px;">{qtd_exec_txt}</td></tr>
                <tr><td style="font-weight:bold; padding:2px 4px;">Serv. Sem Visita (Sobra)</td><td style="padding:2px 4px;">{qtd_des_txt}</td></tr>
                <tr><td style="font-weight:bold; padding:2px 4px;">Serv. totais designados</td><td style="padding:2px 4px;">{qtd_total_servicos_txt}</td></tr>
                <tr><td style="font-weight:bold; padding:2px 4px;">Pontos de rastro veicular</td><td style="padding:2px 4px;">{qtd_rastro_pontos_txt}</td></tr>
            </table>
            </div>
        </div>
        """
        mapa.get_root().html.add_child(Element(resumo_filtros_html))

        icone_mapa_uri = _arquivo_para_data_uri(LOGO_ICON_PATH)
        if icone_mapa_uri:
            icone_mapa_html = f"""
           
            <div style="
                position: fixed;
                bottom: 2px;
                left: 4px;
                z-index: 9998;
                pointer-events: auto;
                display: flex;
                flex-direction: column;
                align-items: left;
            ">
                <a href="https://magoapp.streamlit.app" target="_blank" rel="noopener noreferrer">
                    <img src="{icone_mapa_uri}" alt="Ícone do mapa" style="
                        width: 80px;
                        height: 80px;
                        opacity: 0.50;
                    " />
                </a>
                    <p style="
                        margin: 0;
                        padding: 0;
                        font-size: 8px;
                        line-height: 1;
                        text-align: center;
                        max-width: 500px;
                    ">Monitoramento e Acompanhamento de Gestão Operacional</p>
            </div>
          
            
            """
            mapa.get_root().html.add_child(Element(icone_mapa_html))

        mapa_html = mapa.get_root().render()
        components.html(mapa_html, height=650, scrolling=False)

        data_export = str(data_selecionada).replace("/", "-")
        mes_export = str(mes_selecionado).replace("/", "-")
        equipes_nome_export = _resumo_lista(equipes_selecionadas, limite=2)
        equipes_slug = _normalizar_nome_coluna(equipes_nome_export.replace(", ", "-").replace(" (+", "-mais").replace(")", ""))
        if not equipes_slug:
            equipes_slug = "sem-equipe"
        st.download_button(
            "📥 Exportar mapa filtrado (HTML)",
            data=mapa_html.encode("utf-8"),
            file_name=f"mapa_filtrado_{mes_export}_{data_export}_{equipes_slug}.html",
            mime="text/html",
            use_container_width=False,
        )

        with st.expander("Ver Tabela de Dados Filtrados"):
            colunas_exec = [c for c in [COL_ID, COL_EQUIPE, "Data_BR", COL_HORA_INI, COL_SETOR, COL_RETORNO] if c in df_filtrado.columns]
            if colunas_exec:
                st.dataframe(df_filtrado[colunas_exec], use_container_width=True)
            else:
                st.info("Sem colunas disponíveis para exibir a tabela de serviços executados.")

        if exibir_designados:
            with st.expander("Ver Tabela de Serviços Designados"):
                colunas_designados = [c for c in [COL_D_ID, COL_D_EQUIPE, "Data_BR", COL_D_TIPO, COL_D_ENDERECO] if c in df_designados_filtrado.columns]
                if colunas_designados:
                    st.dataframe(df_designados_filtrado[colunas_designados], use_container_width=True)
                else:
                    st.info("Sem colunas disponíveis para exibir a tabela de designados.")

except Exception as e:
    if e.__class__.__name__ == "StopException":
        raise
    st.error(f"Erro interno ao processar os dados: {e}")
    with st.expander("Detalhes técnicos do erro"):
        st.exception(e)
finally:
    if loading_overlay_slot is not None:
        loading_overlay_slot.empty()
