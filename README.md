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

