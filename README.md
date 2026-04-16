# RotaDiaria

Aplicação em **Streamlit** para visualizar rotas de equipes e comparar:
- serviços **executados** (com rota/linha no mapa);
- serviços **designados pendentes** (sobra do designado que ainda não foi executado).

O mapa é interativo, com filtros por período/data/equipe/setor/status e exportação do estado filtrado em HTML.

---

## Funcionalidades principais

- Autenticação simples por senha (`st.secrets["password"]`).
- Camada de **executados** com:
  - pontos por Código TdC,
  - linha de trajeto por equipe,
  - popups detalhados.
- Camada de **designados (sobra)**:
  - usa `Código Cliente` (designados) ↔ `Instalação` (coordenadas),
  - remove designados já executados (mesma data/equipe selecionada).
- Leitura em produção via Google Sheets (abas `dados`, `designados`, `coordenadas`).
- Exportação do mapa filtrado para HTML:
  - mantém interatividade local (zoom/pan/popup),
  - inclui resumo de filtros no canto do mapa,
  - arquivo nomeado com período/data/equipe.

---

## Estrutura de dados esperada

### Aba `dados` (executados)
Colunas usadas:
- Código TdC
- Equipe
- Latitude
- Longitude
- Data Início
- Data Fim
- Estado TdC
- Resultado
- Tipo TdC
- Causa/Descritivo Resultado
- Ciclo de trabalho

### Aba `designados`
Colunas usadas (com tolerância de nomes via aliases/fuzzy):
- Código TdC
- Código Cliente
- Equipe Designada
- Tipo Serviço
- Estado
- **Data** (prioridade para `Data início Escalonamento`)
- Endereço
- Latitude (opcional)
- Longitude (opcional)

### Aba `coordenadas`
Colunas usadas:
- Instalação
- Latitude
- Longitude

---

## Execução local

## 1. Instalar dependências
```bash
pip install -r requirements.txt
```

## 2. Configurar secrets
Crie `.streamlit/secrets.toml` com:
```toml
password = "SUA_SENHA_APP"
gsheet_id = "ID_DA_PLANILHA"

[gsheet_credentials]
type = "service_account"
project_id = "..."
private_key_id = "..."
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "..."
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "..."
```

## 3. Rodar app
```bash
streamlit run app.py
```

---

## Sincronização SQLite → Google Sheets

Script: `sync_db_to_sheets.py`

Ele sincroniza as abas:
- `dados`
- `designados`
- `coordenadas`

Comportamento:
- cria aba se não existir;
- sanitiza dados e formata coordenadas;
- envia em lotes (`BATCH_SIZE`) para melhor performance em grande volume.

Uso:
```bash
python sync_db_to_sheets.py
```

> Pré-requisito: `credenciais.json` da service account na raiz do projeto.

---

## Deploy (Streamlit Community Cloud)

1. Suba o repositório no GitHub.
2. Configure os secrets no painel do Streamlit Cloud (`password`, `gsheet_id`, `gsheet_credentials`).
3. Garanta que a planilha tenha as abas `dados`, `designados`, `coordenadas` atualizadas.
4. Deploy do `app.py`.

---

## Observações de performance

- O mapa é renderizado como HTML embutido (`components.html`) para evitar reruns a cada pan/zoom.
- Para datasets muito grandes:
  - mantenha sincronização periódica no Sheets;
  - evite excesso de dados fora do período necessário;
  - ajuste `BATCH_SIZE` no script de sync conforme limite da API.

