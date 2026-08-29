from __future__ import annotations

from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd


COLUNAS_ORIGINAIS = {"FULL NAME", "LOCATION", "AREA", "SENIORITY", "Salary"}

COLUNAS_PT_BR = {
    "FULL NAME": "nome_completo",
    "DATE OF BIRTH": "data_nascimento",
    "EDAD": "idade",
    "GENDER": "genero",
    "DATE OF HIRE": "data_contratacao",
    "Date of Termination": "data_desligamento",
    "LOCATION": "localizacao",
    "AREA": "area",
    "SENIORITY": "senioridade",
    "Salary": "salario",
}

VALORES_PT_BR = {
    "localizacao": {
        "Argentina": "Argentina",
        "Brasil": "Brasil",
        "Egipto": "Egito",
        "Espa\u00f1a": "Espanha",
        "Espa\u00ef\u00bf\u00bda": "Espanha",
        "Espa\u00c3\u00b1a": "Espanha",
        "Espa\ufffda": "Espanha",
        "Estados Unidos": "Estados Unidos",
        "India": "\u00cdndia",
        "Mexico": "M\u00e9xico",
    },
    "area": {
        "BI": "BI",
        "Customer Support": "Suporte ao Cliente",
        "Finance": "Financeiro",
        "People": "Pessoas",
        "Product": "Produto",
        "Talent": "Talentos",
        "Tech": "Tecnologia",
        "UX": "UX",
    },
    "senioridade": {
        "Analista Junior": "Analista J\u00fanior",
        "C-Level": "C-Level",
        "Junior": "J\u00fanior",
        "Manager": "Gerente",
        "Semi Senior": "Pleno",
        "Senior": "S\u00eanior",
    },
    "genero": {
        "Femenino": "Feminino",
    },
}


def encontrar_linha_cabecalho_em_dataframe(df: pd.DataFrame) -> int:
    limite = min(len(df), 30)

    for indice in range(limite):
        valores = {
            str(valor).strip()
            for valor in df.iloc[indice].dropna().tolist()
            if str(valor).strip()
        }
        if COLUNAS_ORIGINAIS.issubset(valores):
            return int(indice)

    raise ValueError("Nao encontrei o cabecalho esperado nos dados.")


def encontrar_linha_cabecalho(caminho_csv: Path, encoding: str) -> int:
    pre_visualizacao = pd.read_csv(
        caminho_csv,
        header=None,
        dtype=str,
        encoding=encoding,
        nrows=30,
    )
    return encontrar_linha_cabecalho_em_dataframe(pre_visualizacao)


def normalizar_texto(valor: Any) -> Any:
    if pd.isna(valor):
        return valor
    return str(valor).strip()


def converter_salario_para_numero(valor: Any) -> float | None:
    if pd.isna(valor):
        return None

    texto = str(valor).strip()
    if not texto:
        return None

    texto = texto.replace("$", "").replace(",", "").strip()
    try:
        return float(texto)
    except ValueError:
        return None


def formatar_brl(valor: float | None) -> str:
    if valor is None or pd.isna(valor):
        return ""

    texto = f"R$ {valor:,.2f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


def preparar_dataframe_com_cabecalho(df: pd.DataFrame) -> pd.DataFrame:
    linha_cabecalho = encontrar_linha_cabecalho_em_dataframe(df)
    cabecalho = df.iloc[linha_cabecalho].fillna("").map(str).map(str.strip).tolist()

    dados = df.iloc[linha_cabecalho + 1 :].copy()
    dados.columns = cabecalho
    return dados.reset_index(drop=True)


def transformar_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    if set(COLUNAS_PT_BR).issubset(set(df.columns.astype(str))):
        dados = df.copy()
    else:
        dados = preparar_dataframe_com_cabecalho(df)

    dados = dados.loc[:, ~dados.columns.astype(str).str.startswith("Unnamed")]
    dados = dados.dropna(how="all")
    dados = dados.rename(columns=COLUNAS_PT_BR)

    colunas_esperadas = set(COLUNAS_PT_BR.values())
    colunas_faltantes = sorted(colunas_esperadas.difference(dados.columns))
    if colunas_faltantes:
        raise ValueError(f"Colunas esperadas nao encontradas: {colunas_faltantes}")

    dados = dados[list(COLUNAS_PT_BR.values())].copy()

    for coluna in dados.columns:
        dados[coluna] = dados[coluna].map(normalizar_texto)

    for coluna, mapa in VALORES_PT_BR.items():
        dados[coluna] = dados[coluna].replace(mapa)

    dados["salario_valor"] = dados["salario"].map(converter_salario_para_numero)
    dados["salario"] = dados["salario_valor"].map(formatar_brl)

    dados = dados[dados["nome_completo"].notna() & (dados["nome_completo"] != "")]
    return dados.reset_index(drop=True)


def transformar_csv(caminho_csv: Path, encoding: str) -> pd.DataFrame:
    df = pd.read_csv(caminho_csv, header=None, dtype=str, encoding=encoding)
    return transformar_dataframe(df)


def dataframe_para_csv_download(df: pd.DataFrame) -> bytes:
    buffer = StringIO()
    df.to_csv(buffer, index=False, encoding="utf-8-sig")
    return buffer.getvalue().encode("utf-8-sig")
