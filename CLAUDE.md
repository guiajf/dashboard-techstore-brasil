# CLAUDE.md — Dashboard TechStore Brasil

## Visão Geral do Projeto

Dashboard executivo interativo para a TechStore Brasil (loja de eletrônicos), construído com **Python + Streamlit + Plotly**. Consome dados reais de um arquivo Excel local com ~32.000 transações e 18 meses de histórico.

Stack final será deployada gratuitamente no **Streamlit Community Cloud**.

---

## Arquivos do Projeto

| Arquivo | Descrição |
|---|---|
| `base_vendas_techstore.xlsx` | Base de dados principal (~32k transações, 18 meses) |
| `Prompt.txt` | Especificação completa do projeto |
| `app.py` | Aplicação Streamlit (a ser criada) |
| `requirements.txt` | Dependências Python (a ser criada) |

---

## Schema de Dados (Inferido do Prompt)

> **Atenção:** os nomes exatos das colunas devem ser confirmados lendo `base_vendas_techstore.xlsx` com `pd.read_excel()` antes de qualquer desenvolvimento.

Colunas esperadas na base, derivadas das análises requeridas:

| Coluna (provável) | Tipo | Descrição |
|---|---|---|
| `Data` / `Data_Venda` | date | Data da transação |
| `ID_Pedido` | string/int | Identificador do pedido |
| `Produto` | string | Nome do produto |
| `Categoria` | string | Categoria do produto (ex: Smartphones, Notebooks…) |
| `Canal_Venda` | string | Canal (ex: Online, Físico, Marketplace…) |
| `Região` | string | Região geográfica (ex: Sudeste, Sul…) |
| `Vendedor` | string | Nome do vendedor responsável |
| `Forma_Pagamento` | string | Ex: Cartão Crédito, PIX, Boleto… |
| `Receita` / `Valor_Venda` | float | Valor bruto da venda |
| `Custo` | float | Custo do produto vendido |
| `Lucro` | float | Receita − Custo |
| `Margem` | float | Lucro / Receita × 100 (%) |

---

## Tech Stack

- **Python 3.11+**
- **Streamlit** — framework de UI
- **Plotly Express / Plotly Graph Objects** — todos os gráficos
- **Pandas** — leitura e agregação do Excel
- **openpyxl** — engine de leitura do xlsx

---

## KPIs e Análises Obrigatórias

### Cards de topo (6 KPIs)
1. Receita Total
2. Lucro Total
3. Margem de Lucro (%)
4. Ticket Médio
5. Total de Pedidos
6. Variação vs. período anterior (seta + %) em cada card

### Gráficos (8)
1. Evolução mensal Receita vs Lucro — linha, dois eixos Y
2. Receita por Categoria — donut ou barras horizontais
3. Receita por Canal de Venda — barras verticais
4. Receita por Região — mapa ou barras
5. Top 10 Produtos mais vendidos — barras horizontais
6. Evolução da Margem de Lucro ao longo do tempo — área
7. Vendas por Forma de Pagamento — donut
8. Ranking de Vendedores (Top 5) — barras horizontais

### Tabela final
Resumo mensal: Receita | Custo | Lucro | Margem

---

## Design System (Dark Mode Premium)

### Paleta de Cores
```
Background principal : #0a0a0f
Background cards     : #1a1a24
Acento verde         : #00d4aa  (receita, positivo)
Acento azul          : #4d9fff  (informação)
Acento laranja       : #ff8c42  (alerta, destaque)
Texto primário       : #e8e8f0
Texto secundário     : #8888a0
Borda sutil          : rgba(255,255,255,0.08)
```

### Tipografia
- Fonte: **Inter** (via Google Fonts CSS injection no Streamlit)
- Hierarquia: título → subtítulo → label → valor → caption

### Componentes
- Cards: border-radius 12–16px, sombra suave, glow no hover
- Gráficos: fundo transparente ou com gradiente sutil, sem gridlines agressivas
- Espaçamento generoso entre seções

---

## Formatação de Números

Sempre usar padrão **brasileiro**:
- Moeda: `R$ 1.234.567,89`
- Percentual: `12,34%`
- Inteiros: `32.456`

Implementar com uma função helper centralizada, ex:
```python
def fmt_brl(value: float) -> str:
    return f"R$ {value:_.2f}".replace("_", ".").replace(".", ",", 1)[::-1].replace(",", ".", 1)[::-1]
```
> Ou usar `locale` com `locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')`.

---

## Interatividade

- **Filtro global de período**: seletor no sidebar ou topo — opções: 6 meses / 12 meses / Tudo
- **Tooltips ricos**: valor exato + label formatado ao passar o mouse
- **Hover states** nos cards (leve elevação via CSS injection)
- Animações suaves na entrada (Streamlit `st.spinner` ou Plotly `animation_frame` onde aplicável)

---

## Layout da Aplicação

```
┌─────────────────────────────────────────┐
│  Header: "Dashboard TechStore" + período │
│  Filtro de período (sidebar ou inline)   │
├─────────────────────────────────────────┤
│  [KPI] [KPI] [KPI] [KPI] [KPI] [KPI]   │
├──────────────────┬──────────────────────┤
│  Receita x Lucro │  Receita/Categoria   │
├──────────────────┼──────────────────────┤
│  Receita/Canal   │  Receita/Região      │
├──────────────────┴──────────────────────┤
│  Top 10 Produtos (barras horizontais)   │
├──────────────────┬──────────────────────┤
│  Evolução Margem │  Forma de Pagamento  │
├──────────────────┴──────────────────────┤
│  Ranking de Vendedores (Top 5)          │
├─────────────────────────────────────────┤
│  Tabela: Resumo Mensal                  │
├─────────────────────────────────────────┤
│  Footer: "Dados fictícios — gerado em…" │
└─────────────────────────────────────────┘
```

---

## Deploy (Streamlit Community Cloud)

1. Repositório público no GitHub (ou privado com conta conectada)
2. Arquivo `requirements.txt` com todas as dependências
3. Arquivo `app.py` na raiz do repositório
4. Conectar em [share.streamlit.io](https://share.streamlit.io) e apontar para `app.py`
5. O arquivo `.xlsx` deve estar no repositório (ou migrar para dados embarcados se o arquivo for grande demais para o GitHub)

---

## Convenções de Código

- Arquivo principal: `app.py`
- Sem comentários óbvios; apenas onde a lógica não é autoexplicativa
- Funções helpers separadas no topo do arquivo (formatação, carregamento de dados, paleta)
- `@st.cache_data` obrigatório na função de leitura/aggregação do Excel para performance
- Nenhum número inventado — todos os valores vêm de agregações do DataFrame real
