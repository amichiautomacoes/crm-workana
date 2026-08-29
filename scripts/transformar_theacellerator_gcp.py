from __future__ import annotations

import argparse
import base64
import json
import os
import sys
from pathlib import Path

from dotenv import load_dotenv
from google.cloud import storage
from google.oauth2 import service_account

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.transformacao import transformar_csv


def carregar_credenciais_gcp():
    credencial_base64 = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON_BASE64")
    if credencial_base64:
        credencial_json = base64.b64decode(credencial_base64).decode("utf-8")
        credencial_info = json.loads(credencial_json)
        return service_account.Credentials.from_service_account_info(credencial_info)

    caminho_credencial = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")
    if caminho_credencial:
        return service_account.Credentials.from_service_account_file(caminho_credencial)

    raise RuntimeError(
        "Defina GOOGLE_SERVICE_ACCOUNT_JSON_BASE64 ou GOOGLE_APPLICATION_CREDENTIALS."
    )


def subir_para_gcs(caminho_local: Path, bucket: str, destino: str) -> str:
    credenciais = carregar_credenciais_gcp()
    cliente = storage.Client(
        credentials=credenciais,
        project=getattr(credenciais, "project_id", None),
    )
    blob = cliente.bucket(bucket).blob(destino)
    blob.upload_from_filename(str(caminho_local), content_type="text/csv")
    return f"gs://{bucket}/{destino}"


def criar_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Transforma o CSV The Acellerator para PT-BR e sobe para GCS."
    )
    parser.add_argument(
        "--input",
        default="storage/theacellerator.csv",
        help="Caminho do CSV original.",
    )
    parser.add_argument(
        "--output",
        default="storage/theacellerator_tratado.csv",
        help="Caminho do CSV tratado.",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8",
        help="Encoding do CSV original.",
    )
    parser.add_argument(
        "--bucket",
        default=os.getenv("GCS_BUCKET_NAME") or os.getenv("GCP_BUCKET_NAME"),
        help="Bucket do Google Cloud Storage.",
    )
    parser.add_argument(
        "--destino",
        default=os.getenv("GCS_DESTINATION_BLOB") or "theacellerator_tratado.csv",
        help="Nome/caminho do arquivo dentro do bucket.",
    )
    parser.add_argument(
        "--sem-upload",
        action="store_true",
        help="Apenas gera o CSV tratado localmente.",
    )
    return parser


def main() -> None:
    load_dotenv()
    parser = criar_parser()
    args = parser.parse_args()

    caminho_input = Path(args.input)
    caminho_output = Path(args.output)

    df = transformar_csv(caminho_input, args.encoding)
    caminho_output.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(caminho_output, index=False, encoding="utf-8-sig")

    print(f"CSV tratado salvo em: {caminho_output}")
    print(f"Linhas tratadas: {len(df)}")

    if args.sem_upload:
        print("Upload ignorado por --sem-upload.")
        return

    if not args.bucket:
        print("Upload ignorado: defina GCS_BUCKET_NAME no .env ou use --bucket.")
        return

    uri = subir_para_gcs(caminho_output, args.bucket, args.destino)
    print(f"CSV enviado para: {uri}")


if __name__ == "__main__":
    main()
