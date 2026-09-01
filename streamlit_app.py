from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from dotenv import load_dotenv

from src.google_sheets import ler_google_sheet
from src.transformacao import transformar_dataframe


load_dotenv()

APP_TITLE = "Painel de Rotatividade de Colaboradores"
BACKGROUND_PATH = Path("assets/backgraoundworkana.png")
DATE_COLUMNS = ("data_nascimento", "data_contratacao", "data_desligamento")
FAIXAS_PERMANENCIA = (
    "Até 3 anos",
    "3 a 4 anos",
    "4 a 5 anos",
    "Acima de 5 anos",
)
FAIXAS_IDADE = (
    "Até 25 anos",
    "26 a 35 anos",
    "36 a 45 anos",
    "Acima de 45 anos",
)
FILTROS_PERMANENCIA = {
    "Área": "area",
    "Senioridade": "senioridade",
    "Idade": "idade_faixa",
    "Salário": "salario_faixa",
}
PAIS_ISO3 = {
    "Argentina": "ARG",
    "Brasil": "BRA",
    "Egito": "EGY",
    "Espanha": "ESP",
    "Estados Unidos": "USA",
    "Índia": "IND",
    "México": "MEX",
}
PAGES = (
    "Tempo de permanência",
    "Desligamentos",
)


st.set_page_config(
    page_title=APP_TITLE,
    layout="wide",
)


def carregar_imagem_base64(caminho: Path) -> str:
    return base64.b64encode(caminho.read_bytes()).decode("utf-8")


def aplicar_estilos() -> None:
    background_css = ""
    if BACKGROUND_PATH.exists():
        imagem_base64 = carregar_imagem_base64(BACKGROUND_PATH)
        background_css = f"""
        .stApp {{
            background-image:
                linear-gradient(180deg, rgba(6, 12, 24, .58), rgba(6, 12, 24, .72)),
                url("data:image/png;base64,{imagem_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        """

    st.markdown(
        f"""
        <style>
        {background_css}
        .stApp {{
            background-color: #06101d;
        }}
        [data-testid="stHeader"] {{
            background: rgba(6, 12, 24, .08);
        }}
        .block-container {{
            max-width: 1260px;
            padding-top: 1.4rem;
            padding-bottom: 2.5rem;
        }}
        [data-testid="stSidebar"] {{
            background: rgba(6, 12, 24, .72);
            border-right: 1px solid rgba(255, 255, 255, .18);
        }}
        [data-testid="stSidebar"] * {{
            color: #f8fafc;
        }}
        .page-intro {{
            background:
                linear-gradient(135deg, rgba(255, 255, 255, .94), rgba(241, 245, 249, .88));
            border: 1px solid rgba(255, 255, 255, .7);
            border-radius: 8px;
            box-shadow: 0 20px 54px rgba(0, 0, 0, .24);
            padding: 30px 34px;
            margin-bottom: 24px;
        }}
        .page-intro h1 {{
            color: #0f172a;
            font-size: 2.1rem;
            line-height: 1.1;
            margin: 0 0 10px;
            letter-spacing: 0;
        }}
        .page-intro p {{
            color: #334155;
            font-size: 1.05rem;
            line-height: 1.45;
            margin: 0;
        }}
        .page-intro strong {{
            color: #0f766e;
            font-weight: 800;
        }}
        .metric-grid {{
            display: grid;
            gap: 16px;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            margin-bottom: 24px;
        }}
        .metric-card {{
            background: rgba(255, 255, 255, .94);
            border: 1px solid rgba(226, 232, 240, .86);
            border-radius: 8px;
            box-shadow: 0 16px 42px rgba(0, 0, 0, .2);
            box-sizing: border-box;
            min-height: 132px;
            padding: 22px 24px;
            position: relative;
            overflow: hidden;
        }}
        .metric-card::before {{
            content: "";
            position: absolute;
            inset: 0 auto 0 0;
            width: 5px;
            background: var(--accent);
        }}
        .metric-label {{
            color: #475569;
            font-size: .86rem;
            font-weight: 800;
            line-height: 1.25;
            margin-bottom: 18px;
            text-transform: uppercase;
        }}
        .metric-value {{
            color: #0f172a;
            font-size: 2rem;
            font-weight: 850;
            letter-spacing: 0;
            line-height: 1.08;
            overflow-wrap: anywhere;
            white-space: normal;
        }}
        .metric-value-small {{
            font-size: 1.34rem;
            line-height: 1.15;
        }}
        .metric-detail {{
            color: #64748b;
            font-size: .84rem;
            font-weight: 700;
            line-height: 1.25;
            margin-top: 12px;
        }}
        .chart-section-title {{
            border-left: 6px solid #14b8a6;
            box-sizing: border-box;
            color: #0f172a;
            display: block;
            font-size: 1.48rem;
            font-weight: 850;
            line-height: 1.18;
            letter-spacing: 0;
            margin: 2px 0 20px;
            padding: 2px 0 2px 20px !important;
        }}
        h2.chart-section-title {{
            font-size: 1.48rem !important;
            margin: 2px 0 20px !important;
        }}
        .chart-section-title::before {{
            content: none;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background:
                linear-gradient(145deg, rgba(255, 255, 255, .98), rgba(232, 240, 248, .92));
            border: 1px solid rgba(255, 255, 255, .88);
            border-radius: 8px;
            box-shadow:
                0 28px 70px rgba(0, 0, 0, .34),
                0 10px 22px rgba(15, 23, 42, .16),
                inset 0 1px 0 rgba(255, 255, 255, .92);
            overflow: hidden;
            padding: 24px 26px 18px;
            position: relative;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]::before {{
            content: "";
            position: absolute;
            inset: 0;
            background:
                radial-gradient(circle at 18% 0%, rgba(14, 165, 233, .18), transparent 34%),
                radial-gradient(circle at 88% 16%, rgba(20, 184, 166, .14), transparent 30%);
            pointer-events: none;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] > div {{
            position: relative;
            z-index: 1;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] label {{
            color: #334155;
            font-weight: 750;
        }}
        .scatter-panel-marker {{
            display: none;
        }}
        .dark-panel-marker {{
            display: none;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.scatter-panel-marker),
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.dark-panel-marker) {{
            background:
                radial-gradient(circle at 84% 10%, rgba(99, 102, 241, .22), transparent 28%),
                radial-gradient(circle at 92% 86%, rgba(20, 184, 166, .18), transparent 34%),
                linear-gradient(145deg, rgba(7, 19, 54, .98), rgba(3, 10, 31, .96));
            border: 1px solid rgba(148, 163, 184, .44);
            box-shadow:
                0 34px 90px rgba(0, 0, 0, .42),
                0 12px 28px rgba(15, 23, 42, .28),
                inset 0 1px 0 rgba(255, 255, 255, .18);
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.scatter-panel-marker)::before,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.dark-panel-marker)::before {{
            background:
                linear-gradient(135deg, rgba(255, 255, 255, .08), transparent 42%),
                radial-gradient(circle at 24% 72%, rgba(14, 165, 233, .1), transparent 30%);
        }}
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.scatter-panel-marker) label,
        div[data-testid="stVerticalBlockBorderWrapper"]:has(.dark-panel-marker) label {{
            color: #e2e8f0;
        }}
        .chart-section-title-dark {{
            border-left-color: #38bdf8;
            color: #f8fafc;
        }}
        .styled-table {{
            border-radius: 8px;
            overflow: hidden;
        }}
        @media (max-width: 680px) {{
            .page-intro {{
                padding: 24px 22px;
            }}
            .page-intro h1 {{
                font-size: 1.72rem;
            }}
            .metric-grid {{
                grid-template-columns: 1fr;
            }}
        }}
        @media (min-width: 681px) and (max-width: 1080px) {{
            .metric-grid {{
                grid-template-columns: repeat(2, minmax(0, 1fr));
            }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


@st.cache_data(ttl=300, show_spinner=False)
def carregar_dados() -> pd.DataFrame:
    df_bruto = ler_google_sheet()
    df = transformar_dataframe(df_bruto)
    return enriquecer_rotatividade(df)


def converter_datas(df: pd.DataFrame) -> pd.DataFrame:
    convertido = df.copy()
    for coluna in DATE_COLUMNS:
        convertido[coluna] = pd.to_datetime(
            convertido[coluna],
            dayfirst=True,
            errors="coerce",
        )
    return convertido


def calcular_anos(inicio: pd.Series, fim: pd.Series) -> pd.Series:
    return (fim - inicio).dt.days / 365.25


def enriquecer_rotatividade(df: pd.DataFrame) -> pd.DataFrame:
    dados = converter_datas(df)
    dados["idade_valor"] = pd.to_numeric(
        dados["idade"].astype(str).str.replace(",", ".", regex=False),
        errors="coerce",
    )
    dados["tempo_permanencia_anos"] = calcular_anos(
        dados["data_contratacao"],
        dados["data_desligamento"],
    )
    dados["idade_desligamento"] = calcular_anos(
        dados["data_nascimento"],
        dados["data_desligamento"],
    )
    dados["faixa_permanencia"] = pd.cut(
        dados["tempo_permanencia_anos"],
        bins=[float("-inf"), 3, 4, 5, float("inf")],
        labels=FAIXAS_PERMANENCIA,
        right=True,
    )
    dados["idade_faixa"] = pd.cut(
        dados["idade_valor"],
        bins=[float("-inf"), 25, 35, 45, float("inf")],
        labels=FAIXAS_IDADE,
        right=True,
    )
    dados["salario_faixa"] = pd.cut(
        dados["salario_valor"],
        bins=[float("-inf"), 2000, 4000, 6000, float("inf")],
        labels=("Até R$ 2.000", "R$ 2.001 a R$ 4.000", "R$ 4.001 a R$ 6.000", "Acima de R$ 6.000"),
        right=True,
    )
    dados["ano_contratacao"] = dados["data_contratacao"].dt.year.astype("Int64")
    dados["ano_desligamento"] = dados["data_desligamento"].dt.year.astype("Int64")
    return dados


def render_sidebar() -> str:
    with st.sidebar:
        st.title("Navegação")
        return st.radio(
            "Página",
            PAGES,
            label_visibility="collapsed",
        )


def render_page_intro(titulo: str, subtitulo: str) -> None:
    st.markdown(
        f"""
        <div class="page-intro">
            <h1>{titulo}</h1>
            <p>{subtitulo}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def formatar_anos(valor: float | None) -> str:
    if valor is None or pd.isna(valor):
        return "Sem dados"
    return f"{valor:.1f} anos".replace(".", ",")


def render_metric_card(
    label: str,
    value: str,
    accent: str,
    detail: str = "",
    value_class: str = "",
) -> str:
    detalhe = f'<div class="metric-detail">{detail}</div>' if detail else ""
    classes_valor = f"metric-value {value_class}".strip()
    return (
        f'<article class="metric-card" style="--accent: {accent};">'
        f'<div class="metric-label">{label}</div>'
        f'<div class="{classes_valor}">{value}</div>'
        f"{detalhe}"
        "</article>"
    )


def render_permanencia_cards(df: pd.DataFrame) -> None:
    permanencia = df["tempo_permanencia_anos"].dropna()
    media = permanencia.mean() if not permanencia.empty else None
    mediana = permanencia.median() if not permanencia.empty else None
    maior = permanencia.max() if not permanencia.empty else None
    menor = permanencia.min() if not permanencia.empty else None

    cards = "".join(
        [
            render_metric_card("Média de permanência", formatar_anos(media), "#0ea5e9"),
            render_metric_card("Mediana de permanência", formatar_anos(mediana), "#14b8a6"),
            render_metric_card("Maior permanência", formatar_anos(maior), "#6366f1"),
            render_metric_card("Menor permanência", formatar_anos(menor), "#f97316"),
        ]
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def formatar_numero(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def formatar_decimal(valor: float | None) -> str:
    if valor is None or pd.isna(valor):
        return "Sem dados"
    return f"{valor:.1f}".replace(".", ",")


def opcoes_coluna(df: pd.DataFrame, coluna: str) -> list[str]:
    valores = df[coluna].dropna().astype(str)
    return sorted(valor for valor in valores.unique().tolist() if valor)


def aplicar_filtro_permanencia(df: pd.DataFrame, coluna: str, valores: list[str]) -> pd.DataFrame:
    if not valores:
        return df

    serie = df[coluna].astype(str)
    return df[serie.isin(valores)]


def render_titulo_grafico_permanencia() -> None:
    st.markdown(
        '<h2 class="chart-section-title">Perfil de Retenção e Ciclo de Vida dos Colaboradores</h2>',
        unsafe_allow_html=True,
    )


def render_grafico_perfil_retencao(df: pd.DataFrame) -> None:
    with st.container(border=True):
        render_titulo_grafico_permanencia()

        criterio_col, valores_col, vazio_col = st.columns([1.05, 1.55, 2.4])
        with criterio_col:
            criterio = st.selectbox(
                "Filtrar por",
                list(FILTROS_PERMANENCIA.keys()),
                key="permanencia_filtro_criterio",
            )

        coluna_filtro = FILTROS_PERMANENCIA[criterio]
        with valores_col:
            valores_filtro = st.multiselect(
                criterio,
                opcoes_coluna(df, coluna_filtro),
                key=f"permanencia_filtro_{coluna_filtro}",
                placeholder="Todos",
            )

        with vazio_col:
            st.empty()

        df_filtrado = aplicar_filtro_permanencia(df, coluna_filtro, valores_filtro)
        distribuicao = (
            df_filtrado["faixa_permanencia"]
            .value_counts()
            .reindex(FAIXAS_PERMANENCIA, fill_value=0)
            .rename_axis("Faixa de permanência")
            .reset_index(name="Número de colaboradores")
        )
        total = int(distribuicao["Número de colaboradores"].sum())
        distribuicao["Porcentagem"] = (
            distribuicao["Número de colaboradores"].div(total).mul(100).round(1)
            if total
            else 0
        )
        distribuicao["Legenda"] = distribuicao["Porcentagem"].map(
            lambda valor: f"{valor:.1f}%".replace(".", ",")
        )

        fig = px.bar(
            distribuicao,
            x="Número de colaboradores",
            y="Faixa de permanência",
            orientation="h",
            text="Legenda",
            custom_data=["Porcentagem"],
            color="Faixa de permanência",
            color_discrete_map={
                "Até 3 anos": "#0ea5e9",
                "3 a 4 anos": "#14b8a6",
                "4 a 5 anos": "#6366f1",
                "Acima de 5 anos": "#f97316",
            },
            category_orders={"Faixa de permanência": list(FAIXAS_PERMANENCIA)},
            labels={
                "Número de colaboradores": "Número de colaboradores",
                "Faixa de permanência": "Anos",
            },
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "Anos: %{y}<br>"
                "Número de colaboradores: %{x}<br>"
                "Porcentagem: %{customdata[0]:.1f}%<extra></extra>"
            ),
        )
        fig.update_layout(
            showlegend=True,
            legend_title_text="Porcentagem",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=96, t=14, b=8),
            height=390,
            xaxis=dict(
                title="Número de colaboradores",
                rangemode="tozero",
                dtick=1,
                showgrid=True,
                gridcolor="#e2e8f0",
            ),
            yaxis=dict(
                title="Anos",
                autorange="reversed",
            ),
            font=dict(color="#0f172a"),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_titulo_treemap_permanencia() -> None:
    st.markdown(
        '<h2 class="chart-section-title">Tempo Médio de Permanência</h2>',
        unsafe_allow_html=True,
    )


def render_treemap_permanencia_media(df: pd.DataFrame) -> None:
    opcoes_dimensao = {
        "Senioridade": "senioridade",
        "Área": "area",
        "Idade": "idade_faixa",
    }

    with st.container(border=True):
        render_titulo_treemap_permanencia()

        controle_col, vazio_col = st.columns([1.05, 3.95])
        with controle_col:
            dimensao = st.selectbox(
                "Visualizar por",
                list(opcoes_dimensao.keys()),
                key="treemap_permanencia_dimensao",
            )

        with vazio_col:
            st.empty()

        coluna = opcoes_dimensao[dimensao]
        dados_treemap = (
            df.dropna(subset=[coluna, "tempo_permanencia_anos"])
            .loc[lambda dados: dados[coluna].astype(str).str.strip() != ""]
            .groupby(coluna, observed=False, as_index=False)
            .agg(
                permanencia_media=("tempo_permanencia_anos", "mean"),
                colaboradores=("nome_completo", "count"),
            )
            .sort_values("permanencia_media", ascending=False)
        )

        if dados_treemap.empty:
            st.info("Não há dados suficientes para calcular a permanência média.")
            return

        dados_treemap["permanencia_media"] = dados_treemap[
            "permanencia_media"
        ].round(2)
        dados_treemap["tempo_formatado"] = dados_treemap["permanencia_media"].map(
            formatar_anos
        )
        dados_treemap["colaboradores_label"] = dados_treemap["colaboradores"].map(
            lambda valor: f"{int(valor)} colaboradores"
        )

        fig = px.treemap(
            dados_treemap,
            path=[coluna],
            values="permanencia_media",
            color="permanencia_media",
            color_continuous_scale=["#dc2626", "#f59e0b", "#16a34a"],
            custom_data=[
                "tempo_formatado",
                "colaboradores",
                "colaboradores_label",
            ],
            labels={
                coluna: dimensao,
                "permanencia_media": "Tempo médio de permanência",
            },
        )
        fig.update_traces(
            texttemplate=(
                "<b>%{label}</b><br>"
                "%{customdata[0]}<br>"
                "%{customdata[2]}"
            ),
            textfont=dict(size=18, color="#ffffff"),
            marker=dict(line=dict(width=2, color="rgba(255,255,255,.9)")),
            root_color="rgba(0,0,0,0)",
            hovertemplate=(
                f"{dimensao}: %{{label}}<br>"
                "Tempo médio: %{customdata[0]}<br>"
                "Colaboradores: %{customdata[1]}<extra></extra>"
            ),
        )
        fig.update_layout(
            coloraxis_colorbar=dict(
                title="Anos",
                thickness=14,
                len=0.72,
            ),
            margin=dict(l=8, r=8, t=14, b=8),
            height=470,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a"),
        )

        st.plotly_chart(fig, use_container_width=True)


def formatar_moeda(valor: float | None) -> str:
    if valor is None or pd.isna(valor):
        return "Sem dados"

    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def render_titulo_scatter_salario() -> None:
    st.markdown(
        (
            '<h2 class="chart-section-title chart-section-title-dark">'
            "Relação entre Permanência e Salário"
            "</h2>"
        ),
        unsafe_allow_html=True,
    )


def render_scatter_permanencia_salario(df: pd.DataFrame) -> None:
    opcoes_cor = {
        "Senioridade": "senioridade",
        "Idade": "idade_faixa",
        "Área": "area",
    }

    with st.container(border=True):
        st.markdown('<span class="scatter-panel-marker"></span>', unsafe_allow_html=True)

        titulo_col, filtro_col = st.columns([3.4, 1.2])
        with titulo_col:
            render_titulo_scatter_salario()

        with filtro_col:
            dimensao = st.selectbox(
                "Legenda por",
                list(opcoes_cor.keys()),
                key="scatter_salario_dimensao",
            )

        coluna_cor = opcoes_cor[dimensao]
        dados_scatter = df.dropna(
            subset=["salario_valor", "tempo_permanencia_anos"]
        ).copy()

        if dados_scatter.empty:
            st.info("Não há dados suficientes para cruzar permanência e salário.")
            return

        grupo = dados_scatter[coluna_cor].astype("string").fillna("Sem dados")
        dados_scatter["grupo_legenda"] = grupo.replace("", "Sem dados")
        dados_scatter["salario_formatado"] = dados_scatter["salario_valor"].map(
            formatar_moeda
        )
        dados_scatter["permanencia_formatada"] = dados_scatter[
            "tempo_permanencia_anos"
        ].map(formatar_anos)
        dados_scatter["salario_mil"] = dados_scatter["salario_valor"] / 1000

        fig = px.scatter(
            dados_scatter,
            x="salario_mil",
            y="tempo_permanencia_anos",
            color="grupo_legenda",
            hover_name="nome_completo",
            custom_data=[
                "salario_formatado",
                "permanencia_formatada",
                "grupo_legenda",
                "area",
                "senioridade",
            ],
            labels={
                "salario_mil": "Salário (R$ mil)",
                "tempo_permanencia_anos": "Tempo na empresa",
                "grupo_legenda": dimensao,
            },
            color_discrete_sequence=[
                "#8b5cf6",
                "#06b6d4",
                "#f97316",
                "#14b8a6",
                "#2563eb",
                "#22c55e",
                "#e879f9",
                "#facc15",
            ],
        )

        fig.update_traces(
            marker=dict(
                size=14,
                opacity=0.88,
                line=dict(width=2, color="rgba(255, 255, 255, .86)"),
            ),
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Salário: %{customdata[0]}<br>"
                "Tempo na empresa: %{customdata[1]}<br>"
                f"{dimensao}: %{{customdata[2]}}<br>"
                "Área: %{customdata[3]}<br>"
                "Senioridade: %{customdata[4]}<extra></extra>"
            ),
        )

        salario_medio = dados_scatter["salario_mil"].mean()
        permanencia_media = dados_scatter["tempo_permanencia_anos"].mean()
        fig.add_vline(
            x=salario_medio,
            line_dash="dash",
            line_width=3,
            line_color="rgba(226, 232, 240, .58)",
        )
        fig.add_hline(
            y=permanencia_media,
            line_dash="dash",
            line_width=3,
            line_color="rgba(226, 232, 240, .58)",
        )

        fig.update_layout(
            legend_title_text=dimensao,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=540,
            margin=dict(l=12, r=16, t=18, b=10),
            font=dict(color="#e5e7eb", size=14),
            legend=dict(
                bgcolor="rgba(3, 10, 31, .28)",
                bordercolor="rgba(255,255,255,.14)",
                borderwidth=1,
                font=dict(color="#f8fafc", size=13),
            ),
            xaxis=dict(
                title="Salário (R$ mil)",
                tickprefix="R$ ",
                ticksuffix=" mil",
                separatethousands=False,
                showgrid=True,
                gridcolor="rgba(226, 232, 240, .72)",
                zeroline=False,
                title_font=dict(size=16, color="#f8fafc"),
                tickfont=dict(color="#e5e7eb"),
            ),
            yaxis=dict(
                title="Tempo na empresa",
                ticksuffix=" anos",
                rangemode="tozero",
                showgrid=True,
                gridcolor="rgba(226, 232, 240, .72)",
                zeroline=False,
                title_font=dict(size=16, color="#f8fafc"),
                tickfont=dict(color="#e5e7eb"),
            ),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_titulo_scatter_desligamento_salario() -> None:
    st.markdown(
        (
            '<h2 class="chart-section-title chart-section-title-dark">'
            "Relação entre Desligamento e Salário"
            "</h2>"
        ),
        unsafe_allow_html=True,
    )


def render_scatter_desligamento_salario(df: pd.DataFrame) -> None:
    opcoes_cor = {
        "Senioridade": "senioridade",
        "Idade": "idade_faixa",
        "Área": "area",
    }

    with st.container(border=True):
        st.markdown('<span class="scatter-panel-marker"></span>', unsafe_allow_html=True)

        titulo_col, filtro_col = st.columns([3.4, 1.2])
        with titulo_col:
            render_titulo_scatter_desligamento_salario()

        with filtro_col:
            dimensao = st.selectbox(
                "Legenda por",
                list(opcoes_cor.keys()),
                key="scatter_desligamento_salario_dimensao",
            )

        coluna_cor = opcoes_cor[dimensao]
        dados_scatter = df.dropna(
            subset=["salario_valor", "ano_desligamento", "data_desligamento"]
        ).copy()

        if dados_scatter.empty:
            st.info("Não há dados suficientes para cruzar desligamento e salário.")
            return

        grupo = dados_scatter[coluna_cor].astype("string").fillna("Sem dados")
        dados_scatter["grupo_legenda"] = grupo.replace("", "Sem dados")
        dados_scatter["salario_formatado"] = dados_scatter["salario_valor"].map(
            formatar_moeda
        )
        dados_scatter["data_desligamento_formatada"] = dados_scatter[
            "data_desligamento"
        ].dt.strftime("%d/%m/%Y")
        dados_scatter["salario_mil"] = dados_scatter["salario_valor"] / 1000
        dados_scatter["ano_desligamento_valor"] = dados_scatter[
            "ano_desligamento"
        ].astype(int)

        fig = px.scatter(
            dados_scatter,
            x="salario_mil",
            y="ano_desligamento_valor",
            color="grupo_legenda",
            hover_name="nome_completo",
            custom_data=[
                "salario_formatado",
                "data_desligamento_formatada",
                "grupo_legenda",
                "area",
                "senioridade",
            ],
            labels={
                "salario_mil": "Salário (R$ mil)",
                "ano_desligamento_valor": "Ano de desligamento",
                "grupo_legenda": dimensao,
            },
            color_discrete_sequence=[
                "#8b5cf6",
                "#06b6d4",
                "#f97316",
                "#14b8a6",
                "#2563eb",
                "#22c55e",
                "#e879f9",
                "#facc15",
            ],
        )

        fig.update_traces(
            marker=dict(
                size=14,
                opacity=0.88,
                line=dict(width=2, color="rgba(255, 255, 255, .86)"),
            ),
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Salário: %{customdata[0]}<br>"
                "Desligamento: %{customdata[1]}<br>"
                f"{dimensao}: %{{customdata[2]}}<br>"
                "Área: %{customdata[3]}<br>"
                "Senioridade: %{customdata[4]}<extra></extra>"
            ),
        )

        salario_medio = dados_scatter["salario_mil"].mean()
        ano_medio = dados_scatter["ano_desligamento_valor"].mean()
        fig.add_vline(
            x=salario_medio,
            line_dash="dash",
            line_width=3,
            line_color="rgba(226, 232, 240, .58)",
        )
        fig.add_hline(
            y=ano_medio,
            line_dash="dash",
            line_width=3,
            line_color="rgba(226, 232, 240, .58)",
        )

        anos = dados_scatter["ano_desligamento_valor"]
        fig.update_layout(
            legend_title_text=dimensao,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            height=540,
            margin=dict(l=12, r=16, t=18, b=10),
            font=dict(color="#e5e7eb", size=14),
            legend=dict(
                bgcolor="rgba(3, 10, 31, .28)",
                bordercolor="rgba(255,255,255,.14)",
                borderwidth=1,
                font=dict(color="#f8fafc", size=13),
            ),
            xaxis=dict(
                title="Salário (R$ mil)",
                tickprefix="R$ ",
                ticksuffix=" mil",
                separatethousands=False,
                showgrid=True,
                gridcolor="rgba(226, 232, 240, .72)",
                zeroline=False,
                title_font=dict(size=16, color="#f8fafc"),
                tickfont=dict(color="#e5e7eb"),
            ),
            yaxis=dict(
                title="Ano de desligamento",
                tickmode="linear",
                dtick=1,
                range=[anos.min() - 0.6, anos.max() + 0.6],
                showgrid=True,
                gridcolor="rgba(226, 232, 240, .72)",
                zeroline=False,
                title_font=dict(size=16, color="#f8fafc"),
                tickfont=dict(color="#e5e7eb"),
            ),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_tempo_permanencia(df: pd.DataFrame) -> None:
    render_page_intro(
        "Ciclo de vida dos colaboradores",
        "<strong>Quanto tempo os colaboradores permaneceram na empresa</strong>",
    )
    render_permanencia_cards(df)
    render_grafico_perfil_retencao(df)
    render_treemap_permanencia_media(df)
    render_scatter_permanencia_salario(df)


def render_desligamento_cards(df: pd.DataFrame) -> None:
    desligados = df.dropna(subset=["data_desligamento"]).copy()
    total_desligamentos = len(desligados)

    anos = desligados["ano_desligamento"].dropna().astype(int)
    ano_inicio = int(anos.min()) if not anos.empty else None
    ano_fim = int(anos.max()) if not anos.empty else None
    anos_registro = (ano_fim - ano_inicio + 1) if ano_inicio and ano_fim else None
    media_anual = (
        total_desligamentos / anos_registro
        if total_desligamentos and anos_registro
        else None
    )
    media_salarial = desligados["salario_valor"].dropna().mean()

    periodo = (
        f"{ano_inicio} - {ano_fim}"
        if ano_inicio is not None and ano_fim is not None
        else "Sem dados"
    )
    cards = "".join(
        [
            render_metric_card(
                "Total de desligamentos",
                f"{formatar_numero(total_desligamentos)} colaboradores",
                "#0ea5e9",
                "",
                "metric-value-small",
            ),
            render_metric_card(
                "Período observado",
                periodo,
                "#14b8a6",
            ),
            render_metric_card(
                "Média anual de saídas",
                f"{formatar_decimal(media_anual)} desligamentos/ano",
                "#6366f1",
                "",
                "metric-value-small",
            ),
            render_metric_card(
                "Média salarial por desligado",
                formatar_moeda(media_salarial),
                "#f97316",
                "",
                "metric-value-small",
            ),
        ]
    )
    st.markdown(f'<div class="metric-grid">{cards}</div>', unsafe_allow_html=True)


def render_titulo_evolucao_desligamentos() -> None:
    st.markdown(
        '<h2 class="chart-section-title">Evolução dos Desligamentos</h2>',
        unsafe_allow_html=True,
    )


def render_grafico_evolucao_desligamentos(df: pd.DataFrame) -> None:
    opcoes_dimensao = {
        "Senioridade": "senioridade",
        "Área": "area",
        "Idade": "idade_faixa",
    }

    with st.container(border=True):
        render_titulo_evolucao_desligamentos()

        controle_col, vazio_col = st.columns([1.05, 3.95])
        with controle_col:
            dimensao = st.selectbox(
                "Visualizar por",
                list(opcoes_dimensao.keys()),
                index=1,
                key="evolucao_desligamentos_dimensao",
            )

        with vazio_col:
            st.empty()

        coluna = opcoes_dimensao[dimensao]
        anos = list(range(2012, 2024))
        categorias = opcoes_coluna(df, coluna)
        if coluna == "idade_faixa":
            categorias = [faixa for faixa in FAIXAS_IDADE if faixa in categorias]

        if not categorias:
            st.info("Não há dados suficientes para montar a evolução dos desligamentos.")
            return

        anos_base = pd.MultiIndex.from_product(
            [anos, categorias],
            names=["Ano de desligamento", dimensao],
        ).to_frame(index=False)
        desligamentos_ano = (
            df.dropna(subset=["ano_desligamento", coluna])
            .loc[lambda dados: dados[coluna].astype(str).str.strip() != ""]
            .assign(
                **{
                    "Ano de desligamento": lambda dados: dados[
                        "ano_desligamento"
                    ].astype(int),
                    dimensao: lambda dados: dados[coluna].astype(str),
                }
            )
            .groupby(["Ano de desligamento", dimensao], observed=False, as_index=False)
            .size()
            .rename(columns={"size": "Número de saídas"})
        )
        evolucao = anos_base.merge(
            desligamentos_ano,
            on=["Ano de desligamento", dimensao],
            how="left",
        ).fillna({"Número de saídas": 0})
        evolucao["Número de saídas"] = evolucao["Número de saídas"].astype(int)

        fig = px.line(
            evolucao,
            x="Ano de desligamento",
            y="Número de saídas",
            color=dimensao,
            markers=True,
            labels={
                "Ano de desligamento": "Ano de desligamento",
                "Número de saídas": "Número de saídas",
                dimensao: dimensao,
            },
            color_discrete_sequence=[
                "#0ea5e9",
                "#14b8a6",
                "#6366f1",
                "#f97316",
                "#22c55e",
                "#e879f9",
                "#facc15",
            ],
        )
        fig.update_traces(
            line=dict(width=4, shape="spline", smoothing=0.55),
            marker=dict(
                size=10,
                line=dict(width=2.4, color="#ffffff"),
            ),
            hovertemplate=(
                "Ano: %{x}<br>"
                f"{dimensao}: %{{fullData.name}}<br>"
                "Número de saídas: %{y}<extra></extra>"
            ),
        )

        fig.update_layout(
            showlegend=True,
            legend_title_text=dimensao,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=8, t=14, b=8),
            height=430,
            xaxis=dict(
                title="Ano de desligamento",
                tickmode="linear",
                dtick=1,
                range=[2011.7, 2023.3],
                showgrid=False,
            ),
            yaxis=dict(
                title="Número de saídas",
                rangemode="tozero",
                dtick=1,
                showgrid=True,
                gridcolor="#e2e8f0",
            ),
            font=dict(color="#0f172a"),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_titulo_mapa_desligamentos() -> None:
    st.markdown(
        '<h2 class="chart-section-title">Distribuição Geográfica dos Desligamentos</h2>',
        unsafe_allow_html=True,
    )


def render_mapa_desligamentos(df: pd.DataFrame) -> None:
    with st.container(border=True):
        render_titulo_mapa_desligamentos()

        desligados = (
            df.dropna(subset=["data_desligamento", "localizacao", "ano_desligamento"])
            .loc[lambda dados: dados["localizacao"].astype(str).str.strip() != ""]
            .assign(
                iso3=lambda dados: dados["localizacao"].map(PAIS_ISO3),
                ano=lambda dados: dados["ano_desligamento"].astype(int),
            )
            .dropna(subset=["iso3"])
        )

        if desligados.empty:
            st.info("Não há países reconhecidos para exibir no mapa.")
            return

        linhas = []
        for pais, grupo in desligados.groupby("localizacao", sort=True):
            por_ano = (
                grupo.groupby("ano")
                .size()
                .rename("saidas")
                .reset_index()
                .sort_values("ano")
            )
            detalhe_anos = "<br>".join(
                f"{int(linha.ano)}: {int(linha.saidas)} saída(s)"
                for linha in por_ano.itertuples(index=False)
            )
            linhas.append(
                {
                    "País": pais,
                    "iso3": grupo["iso3"].iloc[0],
                    "Desligamentos": len(grupo),
                    "Quando": detalhe_anos,
                }
            )

        dados_mapa = pd.DataFrame(linhas).sort_values(
            "Desligamentos",
            ascending=False,
        )

        fig = px.choropleth(
            dados_mapa,
            locations="iso3",
            locationmode="ISO-3",
            color="Desligamentos",
            hover_name="País",
            custom_data=["Desligamentos", "Quando"],
            color_continuous_scale=["#dbeafe", "#38bdf8", "#f97316"],
            labels={"Desligamentos": "Desligamentos"},
        )
        fig.update_traces(
            marker_line_color="rgba(255,255,255,.88)",
            marker_line_width=0.9,
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Desligamentos: %{customdata[0]}<br><br>"
                "%{customdata[1]}<extra></extra>"
            ),
        )
        fig.update_layout(
            coloraxis_colorbar=dict(
                title="Saídas",
                thickness=14,
                len=0.72,
            ),
            margin=dict(l=8, r=8, t=14, b=8),
            height=520,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(color="#0f172a"),
            geo=dict(
                bgcolor="rgba(0,0,0,0)",
                projection_type="natural earth",
                showframe=False,
                showcoastlines=True,
                coastlinecolor="rgba(15, 23, 42, .32)",
                showcountries=True,
                countrycolor="rgba(15, 23, 42, .24)",
                showland=True,
                landcolor="rgba(248, 250, 252, .7)",
                showocean=True,
                oceancolor="rgba(14, 165, 233, .12)",
            ),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_treemap_desligamentos(df: pd.DataFrame) -> None:
    opcoes_dimensao = {
        "Senioridade": "senioridade",
        "Área": "area",
        "Idade": "idade_faixa",
    }

    with st.container(border=True):
        st.markdown('<span class="dark-panel-marker"></span>', unsafe_allow_html=True)

        titulo_col, filtro_col = st.columns([3.4, 1.2])
        with filtro_col:
            dimensao = st.selectbox(
                "Visualizar por",
                list(opcoes_dimensao.keys()),
                index=1,
                key="treemap_desligamentos_dimensao",
            )

        with titulo_col:
            st.markdown(
                (
                    '<h2 class="chart-section-title chart-section-title-dark">'
                    f"Desligamentos por {dimensao}"
                    "</h2>"
                ),
                unsafe_allow_html=True,
            )

        coluna = opcoes_dimensao[dimensao]
        dados_treemap = (
            df.dropna(subset=["data_desligamento", coluna])
            .loc[lambda dados: dados[coluna].astype(str).str.strip() != ""]
            .groupby(coluna, observed=False, as_index=False)
            .agg(
                desligamentos=("nome_completo", "count"),
                salario_medio=("salario_valor", "mean"),
            )
            .sort_values("desligamentos", ascending=False)
        )

        if dados_treemap.empty:
            st.info("Não há dados suficientes para montar o treemap de desligamentos.")
            return

        dados_treemap["label_desligamentos"] = dados_treemap["desligamentos"].map(
            lambda valor: (
                f"{int(valor)} desligamento"
                if int(valor) == 1
                else f"{int(valor)} desligamentos"
            )
        )
        dados_treemap["salario_medio_formatado"] = dados_treemap[
            "salario_medio"
        ].map(formatar_moeda)

        fig = px.treemap(
            dados_treemap,
            path=[coluna],
            values="desligamentos",
            color="desligamentos",
            color_continuous_scale=["#dbeafe", "#22d3ee", "#f97316"],
            custom_data=[
                "label_desligamentos",
                "salario_medio_formatado",
            ],
            labels={
                coluna: dimensao,
                "desligamentos": "Desligamentos",
            },
        )
        fig.update_traces(
            texttemplate="<b>%{label}</b><br>%{customdata[0]}",
            textfont=dict(size=17, color="#0f172a"),
            marker=dict(line=dict(width=3, color="#ffffff")),
            root_color="rgba(255,255,255,.24)",
            hovertemplate=(
                f"{dimensao}: %{{label}}<br>"
                "%{customdata[0]}<br>"
                "Média salarial: %{customdata[1]}<extra></extra>"
            ),
        )
        fig.update_layout(
            coloraxis_showscale=False,
            margin=dict(l=8, r=8, t=14, b=8),
            height=500,
            paper_bgcolor="rgba(255,255,255,.92)",
            plot_bgcolor="rgba(255,255,255,.92)",
            font=dict(color="#0f172a"),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_desligamentos(df: pd.DataFrame) -> None:
    render_page_intro(
        "Análise do desligamento dos colaboradores",
        (
            "Mapeia o <strong>ritmo</strong>, a <strong>geografia</strong> "
            "e o <strong>impacto financeiro</strong> da desmobilização da equipe "
            "ao longo dos anos."
        ),
    )
    render_desligamento_cards(df)
    render_grafico_evolucao_desligamentos(df)
    render_mapa_desligamentos(df)
    render_treemap_desligamentos(df)
    render_scatter_desligamento_salario(df)


def main() -> None:
    aplicar_estilos()
    pagina = render_sidebar()

    try:
        df = carregar_dados()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar a planilha: {exc}")
        st.stop()

    if pagina == "Tempo de permanência":
        render_tempo_permanencia(df)
    elif pagina == "Desligamentos":
        render_desligamentos(df)


if __name__ == "__main__":
    main()
