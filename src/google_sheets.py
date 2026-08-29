from __future__ import annotations

import base64
import json
import os
import re
from pathlib import Path

import gspread
import pandas as pd
from google.oauth2 import service_account


DEFAULT_SPREADSHEET_ID = "15dKhTE2tJWXRlSCsrp4YafsnjWhpNhGuWgi3zJ-6xJE"
GOOGLE_SCOPES = (
    "https://www.googleapis.com/auth/spreadsheets.readonly",
    "https://www.googleapis.com/auth/drive.readonly",
)


def extrair_spreadsheet_id(valor: str) -> str:
    texto = valor.strip()
    match = re.search(r"/spreadsheets/d/([^/]+)", texto)
    return match.group(1) if match else texto


def carregar_credenciais_google():
    credencial_base64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
    if credencial_base64:
        credencial_json = base64.b64decode(credencial_base64).decode("utf-8")
        credencial_info = json.loads(credencial_json)
        return service_account.Credentials.from_service_account_info(
            credencial_info,
            scopes=GOOGLE_SCOPES,
        )

    caminho_credencial = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if caminho_credencial:
        return service_account.Credentials.from_service_account_file(
            Path(caminho_credencial),
            scopes=GOOGLE_SCOPES,
        )

    raise RuntimeError(
        "Defina GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 ou GOOGLE_APPLICATION_CREDENTIALS."
    )


def ler_google_sheet(
    spreadsheet_id: str | None = None,
    worksheet_name: str | None = None,
) -> pd.DataFrame:
    chave = extrair_spreadsheet_id(
        spreadsheet_id
        or os.getenv("GOOGLE_SHEET_ID")
        or os.getenv("GOOGLE_SHEET_URL")
        or DEFAULT_SPREADSHEET_ID
    )
    aba = worksheet_name or os.getenv("GOOGLE_SHEET_WORKSHEET")

    cliente = gspread.authorize(carregar_credenciais_google())
    planilha = cliente.open_by_key(chave)
    worksheet = planilha.worksheet(aba) if aba else planilha.sheet1
    valores = worksheet.get_all_values()

    if not valores:
        raise ValueError("A planilha nao retornou dados.")

    return pd.DataFrame(valores)
