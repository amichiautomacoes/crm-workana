from __future__ import annotations

import base64
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

from src.google_sheets import ler_google_sheet
from src.transformacao import dataframe_para_csv_download, transformar_dataframe


load_dotenv()

APP_TITLE = "Painel de Rotatividade de Colaboradores"
BACKGROUND_PATH = Path("assets/backgraoundworkana.png")
DATE_COLUMNS = ("data_nascimento", "data_contratacao", "data_desligamento")
FAIXAS_PERMANENCIA = (
    "Ate 3 anos",
    "3 a 4 anos",
    "4 a 5 anos",
    "Mais de 5 anos",
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
                linear-gradient(180deg, rgba(246, 248, 251, .76), rgba(246, 248, 251, .9)),
                url("data:image/png;base64,{imagem_base64}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .hero {{
            background-image:
                linear-gradient(90deg, rgba(5, 16, 46, .96), rgba(5, 16, 46, .58)),
                url("data:image/png;base64,{imagem_base64}");
        }}
        """

    st.markdown(
        f"""
        <style>
        {background_css}
        .stApp {{
            background-color: #f6f8fb;
        }}
        .block-container {{
            padding-top: 1.1rem;
            padding-bottom: 2.2rem;
            max-width: 1360px;
        }}
        .hero {{
            min-height: 220px;
            border-radius: 8px;
            padding: 38px 42px;
            color: white;
            margin-bottom: 22px;
            display: flex;
            flex-direction: column;
            justify-content: center;
            box-shadow: 0 22px 60px rgba(10, 21, 52, .16);
            background-size: cover;
            background-position: center;
        }}
        .hero-label {{
            color: #67e8f9;
            font-size: .78rem;
            font-weight: 800;
            letter-spacing: .08em;
            margin-bottom: 12px;
            text-transform: uppercase;
        }}
        .hero h1 {{
            font-size: 2.65rem;
            line-height: 1.05;
            margin: 0 0 10px;
            letter-spacing: 0;
            max-width: 760px;
        }}
        .hero p {{
            max-width: 720px;
            margin: 0;
            color: rgba(255,255,255,.84);
            font-size: 1.02rem;
        }}
        .metric-card {{
            background: #ffffff;
            border: 1px solid #e5e9f2;
            border-radius: 8px;
            padding: 18px 18px 16px;
            min-height: 136px;
            box-shadow: 0 14px 30px rgba(15, 23, 42, .06);
            position: relative;
            overflow: hidden;
        }}
        .metric-card::before {{
            content: "";
            position: absolute;
            left: 0;
            top: 0;
            width: 100%;
            height: 4px;
            background: var(--accent);
        }}
        .metric-label {{
            color: #667085;
            font-size: .82rem;
            font-weight: 700;
            line-height: 1.25;
            min-height: 34px;
        }}
        .metric-value {{
            color: #111827;
            font-size: 2rem;
            font-weight: 800;
            line-height: 1.05;
            margin-top: 10px;
        }}
        .metric-note {{
            color: #7a8599;
            font-size: .78rem;
            margin-top: 8px;
        }}
        .section-title {{
            color: #111827;
            font-size: 1.05rem;
            font-weight: 800;
            margin: 4px 0 10px;
        }}
        .chart-title {{
            color: #111827;
            font-size: 1.08rem;
            font-weight: 800;
            line-height: 1.2;
            margin: 2px 0 14px;
        }}
        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background: rgba(255, 255, 255, .92);
            border: 1px solid rgba(229, 233, 242, .96);
            border-radius: 8px;
            box-shadow: 0 18px 40px rgba(15, 23, 42, .08);
            padding: 18px 20px 16px;
        }}
        .stDataFrame {{
            border: 1px solid #e5e9f2;
            border-radius: 8px;
        }}
        [data-testid="stSidebar"] {{
            background: #ffffff;
            border-right: 1px solid #e5e9f2;
        }}
        @media (max-width: 680px) {{
            .hero {{
                padding: 28px 24px;
                min-height: 210px;
            }}
            .hero h1 {{
                font-size: 2rem;
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
    dados["ano_contratacao"] = dados["data_contratacao"].dt.year.astype("Int64")
    dados["ano_desligamento"] = dados["data_desligamento"].dt.year.astype("Int64")
    return dados


def opcoes_coluna(df: pd.DataFrame, coluna: str) -> list[str]:
    return sorted(valor for valor in df[coluna].dropna().unique().tolist() if valor)


def opcoes_ano(df: pd.DataFrame, coluna: str) -> list[int]:
    return sorted(int(valor) for valor in df[coluna].dropna().unique().tolist())


def descrever_filtro_anos(anos_selecionados: list[int], anos_disponiveis: list[int]) -> str:
    anos = anos_selecionados or anos_disponiveis
    if not anos:
        return "Sem periodo"

    if len(anos) == 1:
        return str(anos[0])

    return f"{min(anos)} a {max(anos)}"


def aplicar_filtros(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    anos_contratacao_disponiveis = opcoes_ano(df, "ano_contratacao")
    anos_desligamento_disponiveis = opcoes_ano(df, "ano_desligamento")

    with st.sidebar:
        st.header("Filtros interativos")
        localizacoes = st.multiselect("Pais", opcoes_coluna(df, "localizacao"))
        areas = st.multiselect("Area", opcoes_coluna(df, "area"))
        senioridades = st.multiselect("Senioridade", opcoes_coluna(df, "senioridade"))
        generos = st.multiselect("Genero", opcoes_coluna(df, "genero"))
        anos_contratacao = st.multiselect(
            "Ano de contratacao",
            anos_contratacao_disponiveis,
        )
        anos_desligamento = st.multiselect(
            "Ano de desligamento",
            anos_desligamento_disponiveis,
        )

    filtrado = df.copy()
    if localizacoes:
        filtrado = filtrado[filtrado["localizacao"].isin(localizacoes)]
    if areas:
        filtrado = filtrado[filtrado["area"].isin(areas)]
    if senioridades:
        filtrado = filtrado[filtrado["senioridade"].isin(senioridades)]
    if generos:
        filtrado = filtrado[filtrado["genero"].isin(generos)]
    if anos_contratacao:
        filtrado = filtrado[filtrado["ano_contratacao"].isin(anos_contratacao)]
    if anos_desligamento:
        filtrado = filtrado[filtrado["ano_desligamento"].isin(anos_desligamento)]

    periodo_desligamento = descrever_filtro_anos(
        anos_desligamento,
        anos_desligamento_disponiveis,
    )
    return filtrado, periodo_desligamento


def formatar_numero(valor: int) -> str:
    return f"{valor:,}".replace(",", ".")


def formatar_anos(valor: float) -> str:
    if pd.isna(valor):
        return "Sem dados"
    return f"{valor:.1f} anos".replace(".", ",")


def render_metric_card(label: str, value: str, note: str, accent: str) -> None:
    st.markdown(
        f"""
        <div class="metric-card" style="--accent: {accent};">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-note">{note}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_visao_geral(
    df: pd.DataFrame,
    periodo_desligamento: str,
) -> None:
    total_colaboradores = len(df)
    tempo_medio = df["tempo_permanencia_anos"].dropna().mean()
    idade_media = df["idade_desligamento"].dropna().mean()
    desligamentos = df["data_desligamento"].notna().sum()

    st.markdown('<div class="section-title">Visao geral</div>', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        render_metric_card(
            "Total de colaboradores analisados",
            formatar_numero(total_colaboradores),
            "Base apos filtros aplicados",
            "#06b6d4",
        )
    with col2:
        render_metric_card(
            "Tempo medio de permanencia",
            formatar_anos(tempo_medio),
            "Da contratacao ao desligamento",
            "#14b8a6",
        )
    with col3:
        render_metric_card(
            "Idade media no desligamento",
            formatar_anos(idade_media),
            "Valor aproximado por datas",
            "#8b5cf6",
        )
    with col4:
        render_metric_card(
            "Desligamentos no periodo",
            formatar_numero(int(desligamentos)),
            periodo_desligamento,
            "#f97316",
        )


def render_evolucao_desligamentos(df: pd.DataFrame) -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="chart-title">Evolu\u00e7\u00e3o dos desligamentos</div>',
            unsafe_allow_html=True,
        )

        evolucao = (
            df.dropna(subset=["data_desligamento"])
            .assign(ano=lambda dados: dados["data_desligamento"].dt.year)
            .groupby("ano", as_index=False)
            .size()
            .rename(columns={"ano": "Ano", "size": "Desligamentos"})
            .sort_values("Ano")
        )

        fig = px.line(
            evolucao,
            x="Ano",
            y="Desligamentos",
            markers=True,
            labels={"Ano": "Ano", "Desligamentos": "Quantidade de desligamentos"},
            color_discrete_sequence=["#06b6d4"],
        )
        fig.update_traces(
            line=dict(width=3),
            marker=dict(size=9, color="#06b6d4", line=dict(width=2, color="#ffffff")),
            hovertemplate="Ano %{x}<br>Desligamentos: %{y}<extra></extra>",
        )
        fig.update_layout(
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=8, t=8, b=8),
            xaxis=dict(dtick=1, tickmode="linear", showgrid=False),
            yaxis=dict(title="Quantidade de desligamentos", rangemode="tozero", dtick=1),
            hovermode="x unified",
        )

        st.plotly_chart(fig, use_container_width=True)


def render_tempo_permanencia(df: pd.DataFrame) -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="chart-title">Tempo de Perman\u00eancia na Empresa</div>',
            unsafe_allow_html=True,
        )

        distribuicao = (
            df["faixa_permanencia"]
            .value_counts()
            .reindex(FAIXAS_PERMANENCIA, fill_value=0)
            .rename_axis("Faixa")
            .reset_index(name="Colaboradores")
        )
        total = int(distribuicao["Colaboradores"].sum())
        distribuicao["Percentual"] = (
            distribuicao["Colaboradores"].div(total).mul(100).round(1) if total else 0
        )
        distribuicao["Rotulo"] = distribuicao.apply(
            lambda linha: (
                f"{int(linha['Colaboradores'])} colaboradores "
                f"({linha['Percentual']:.1f}%)".replace(".", ",")
            ),
            axis=1,
        )

        fig = px.bar(
            distribuicao,
            x="Colaboradores",
            y="Faixa",
            orientation="h",
            text="Rotulo",
            color="Faixa",
            color_discrete_map={
                "Ate 3 anos": "#06b6d4",
                "3 a 4 anos": "#14b8a6",
                "4 a 5 anos": "#8b5cf6",
                "Mais de 5 anos": "#f97316",
            },
            category_orders={"Faixa": list(FAIXAS_PERMANENCIA)},
            custom_data=["Percentual"],
        )
        fig.update_traces(
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "%{y}<br>"
                "Colaboradores: %{x}<br>"
                "Participacao: %{customdata[0]:.1f}%<extra></extra>"
            ),
        )
        fig.update_layout(
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=128, t=8, b=8),
            xaxis=dict(
                title="Quantidade de colaboradores",
                rangemode="tozero",
                dtick=1,
                showgrid=True,
                gridcolor="#e5e9f2",
            ),
            yaxis=dict(title="", autorange="reversed"),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_heatmap_permanencia_media(df: pd.DataFrame) -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="chart-title">Tempo M\u00e9dio de Perman\u00eancia</div>',
            unsafe_allow_html=True,
        )

        chart_col, selector_col = st.columns([4, 1])
        with selector_col:
            dimensao = st.selectbox(
                "Visualizar por",
                ("\u00c1rea", "Cargo"),
                key="heatmap_permanencia_dimensao",
            )

        coluna = "area" if dimensao == "\u00c1rea" else "senioridade"
        rotulo_dimensao = "\u00c1rea" if dimensao == "\u00c1rea" else "Cargo"
        dados_heatmap = (
            df.dropna(subset=[coluna, "tempo_permanencia_anos"])
            .loc[lambda dados: dados[coluna] != ""]
            .groupby(coluna, as_index=False)
            .agg(
                permanencia_media=("tempo_permanencia_anos", "mean"),
                colaboradores=("nome_completo", "count"),
            )
            .sort_values("permanencia_media", ascending=False)
        )

        with chart_col:
            if dados_heatmap.empty:
                st.info(
                    "N\u00e3o h\u00e1 dados suficientes para calcular perman\u00eancia "
                    "m\u00e9dia."
                )
                return

            dados_heatmap["permanencia_media"] = dados_heatmap[
                "permanencia_media"
            ].round(1)
            valores = dados_heatmap["permanencia_media"].tolist()
            categorias = dados_heatmap[coluna].tolist()
            textos = [[formatar_anos(valor) for valor in valores]]
            customdata = [dados_heatmap["colaboradores"].tolist()]

            fig = go.Figure(
                data=go.Heatmap(
                    z=[valores],
                    x=categorias,
                    y=["Tempo m\u00e9dio"],
                    text=textos,
                    customdata=customdata,
                    texttemplate="%{text}",
                    textfont=dict(color="#111827", size=14),
                    colorscale=[
                        [0, "#e0f2fe"],
                        [0.5, "#22d3ee"],
                        [1, "#f97316"],
                    ],
                    colorbar=dict(
                        title="Anos",
                        thickness=14,
                        len=0.72,
                    ),
                    hovertemplate=(
                        f"{rotulo_dimensao}: %{{x}}<br>"
                        "Tempo m\u00e9dio: %{z:.1f} anos<br>"
                        "Colaboradores: %{customdata}<extra></extra>"
                    ),
                )
            )
            fig.update_layout(
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                margin=dict(l=8, r=8, t=8, b=8),
                height=310,
                xaxis=dict(
                    title=rotulo_dimensao,
                    tickangle=0,
                    side="bottom",
                    automargin=True,
                ),
                yaxis=dict(title=""),
            )

            st.plotly_chart(fig, use_container_width=True)


def render_salario_permanencia(df: pd.DataFrame) -> None:
    with st.container(border=True):
        st.markdown(
            '<div class="chart-title">Rela\u00e7\u00e3o entre Sal\u00e1rio e Perman\u00eancia</div>',
            unsafe_allow_html=True,
        )

        dispersao = df.dropna(subset=["salario_valor", "tempo_permanencia_anos"]).copy()

        if dispersao.empty:
            st.info("Nao ha dados suficientes para cruzar salario e permanencia.")
            return

        fig = px.scatter(
            dispersao,
            x="salario_valor",
            y="tempo_permanencia_anos",
            color="senioridade",
            hover_name="nome_completo",
            hover_data={
                "salario_valor": ":,.2f",
                "tempo_permanencia_anos": ":.1f",
                "senioridade": True,
                "area": True,
                "localizacao": True,
            },
            labels={
                "salario_valor": "Salario",
                "tempo_permanencia_anos": "Tempo na empresa",
                "senioridade": "Senioridade",
                "area": "Area",
                "localizacao": "Localizacao",
            },
            color_discrete_map={
                "Pleno": "#06b6d4",
                "Analista J\u00fanior": "#14b8a6",
                "S\u00eanior": "#8b5cf6",
                "Gerente": "#f97316",
                "C-Level": "#2563eb",
            },
        )
        fig.update_traces(
            marker=dict(size=12, opacity=0.82, line=dict(width=1.5, color="#ffffff")),
            hovertemplate=(
                "<b>%{hovertext}</b><br>"
                "Salario: R$ %{x:,.2f}<br>"
                "Tempo na empresa: %{y:.1f} anos<br>"
                "Senioridade: %{customdata[2]}<br>"
                "Area: %{customdata[3]}<br>"
                "Localizacao: %{customdata[4]}<extra></extra>"
            ),
        )

        salario_medio = dispersao["salario_valor"].mean()
        permanencia_media = dispersao["tempo_permanencia_anos"].mean()
        fig.add_vline(
            x=salario_medio,
            line_dash="dash",
            line_color="#94a3b8",
            opacity=0.8,
        )
        fig.add_hline(
            y=permanencia_media,
            line_dash="dash",
            line_color="#94a3b8",
            opacity=0.8,
        )
        fig.update_layout(
            legend_title_text="Senioridade",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=8, r=8, t=8, b=8),
            xaxis=dict(
                title="Salario",
                tickprefix="R$ ",
                separatethousands=True,
                showgrid=True,
                gridcolor="#e5e9f2",
            ),
            yaxis=dict(
                title="Tempo na empresa",
                ticksuffix=" anos",
                rangemode="tozero",
                showgrid=True,
                gridcolor="#e5e9f2",
            ),
        )

        st.plotly_chart(fig, use_container_width=True)


def render_graficos(df: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)

    por_area = df.groupby("area", as_index=False).size().sort_values("size", ascending=False)
    fig_area = px.bar(
        por_area,
        x="area",
        y="size",
        labels={"area": "Area", "size": "Desligamentos"},
        color_discrete_sequence=["#14b8a6"],
    )
    fig_area.update_layout(
        title="Desligamentos por area",
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=48, b=8),
    )
    col1.plotly_chart(fig_area, use_container_width=True)

    por_senioridade = (
        df.groupby("senioridade", as_index=False).size().sort_values("size", ascending=False)
    )
    fig_senioridade = px.bar(
        por_senioridade,
        x="senioridade",
        y="size",
        labels={"senioridade": "Senioridade", "size": "Desligamentos"},
        color_discrete_sequence=["#8b5cf6"],
    )
    fig_senioridade.update_layout(
        title="Desligamentos por senioridade",
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=8, r=8, t=48, b=8),
    )
    col2.plotly_chart(fig_senioridade, use_container_width=True)


def preparar_tabela(df: pd.DataFrame) -> pd.DataFrame:
    tabela = df.copy()
    for coluna in DATE_COLUMNS:
        tabela[coluna] = tabela[coluna].dt.strftime("%d/%m/%Y")
    tabela["tempo_permanencia_anos"] = tabela["tempo_permanencia_anos"].round(1)
    tabela["idade_desligamento"] = tabela["idade_desligamento"].round(1)
    return tabela


def main() -> None:
    aplicar_estilos()

    st.markdown(
        """
        <section class="hero">
            <div class="hero-label">People Analytics</div>
            <h1>Painel de Rotatividade de Colaboradores</h1>
            <p>Analise de desligamentos, permanencia e perfil dos colaboradores a partir da base oficial no Google Sheets.</p>
        </section>
        """,
        unsafe_allow_html=True,
    )

    try:
        df = carregar_dados()
    except Exception as exc:
        st.error(f"Nao foi possivel carregar a planilha: {exc}")
        st.stop()

    df_filtrado, periodo_desligamento = aplicar_filtros(df)

    render_visao_geral(df_filtrado, periodo_desligamento)

    if df_filtrado.empty:
        st.info("Nenhum desligamento encontrado para os filtros selecionados.")
        st.stop()

    render_evolucao_desligamentos(df_filtrado)
    st.divider()

    render_tempo_permanencia(df_filtrado)
    st.divider()

    render_heatmap_permanencia_media(df_filtrado)
    st.divider()

    render_salario_permanencia(df_filtrado)
    st.divider()

    render_graficos(df_filtrado)
    st.divider()

    col1, col2 = st.columns([1, 3])
    col1.download_button(
        "Baixar CSV",
        data=dataframe_para_csv_download(preparar_tabela(df_filtrado)),
        file_name="rotatividade_colaboradores.csv",
        mime="text/csv",
        use_container_width=True,
    )
    col2.caption(f"{len(df_filtrado)} registros exibidos apos os filtros aplicados.")

    st.dataframe(
        preparar_tabela(df_filtrado),
        use_container_width=True,
        hide_index=True,
        column_order=(
            "nome_completo",
            "localizacao",
            "area",
            "senioridade",
            "data_contratacao",
            "ano_contratacao",
            "data_desligamento",
            "ano_desligamento",
            "tempo_permanencia_anos",
            "idade_desligamento",
            "salario",
        ),
        column_config={
            "nome_completo": st.column_config.TextColumn("Colaborador", width="large"),
            "localizacao": st.column_config.TextColumn("Localizacao", width="medium"),
            "area": st.column_config.TextColumn("Area", width="medium"),
            "senioridade": st.column_config.TextColumn("Senioridade", width="medium"),
            "data_contratacao": st.column_config.TextColumn("Contratacao", width="small"),
            "ano_contratacao": st.column_config.NumberColumn(
                "Ano contratacao",
                format="%d",
                width="small",
            ),
            "data_desligamento": st.column_config.TextColumn("Desligamento", width="small"),
            "ano_desligamento": st.column_config.NumberColumn(
                "Ano desligamento",
                format="%d",
                width="small",
            ),
            "tempo_permanencia_anos": st.column_config.NumberColumn(
                "Permanencia",
                format="%.1f anos",
                width="small",
            ),
            "idade_desligamento": st.column_config.NumberColumn(
                "Idade no desligamento",
                format="%.1f anos",
                width="small",
            ),
            "salario": st.column_config.TextColumn("Salario", width="small"),
        },
    )


if __name__ == "__main__":
    main()
