# Painel de Rotatividade de Colaboradores

Aplicacao Streamlit para consultar e analisar rotatividade de colaboradores a partir da base The Acellerator no Google Sheets.

## Arquitetura

```text
Google Sheets -> Streamlit -> EasyPanel
```

- Google Sheets: fonte dos dados brutos.
- Streamlit: leitura, tratamento, filtros, metricas, graficos e download do CSV tratado.
- EasyPanel: deploy da aplicacao em container Docker.

## Estrutura

```text
.
+-- assets/
|   +-- backgraoundworkana.png
+-- scripts/
|   +-- transformar_theacellerator_gcp.py
+-- src/
|   +-- google_sheets.py
|   +-- transformacao.py
+-- streamlit_app.py
+-- Dockerfile
+-- .dockerignore
+-- .env.example
+-- requirements.txt
```

## Fonte de dados

Planilha configurada:

```text
https://docs.google.com/spreadsheets/d/15dKhTE2tJWXRlSCsrp4YafsnjWhpNhGuWgi3zJ-6xJE/edit
```

A service account autorizada na planilha e:

```text
crm-workana@crm-workana.iam.gserviceaccount.com
```

Por padrao, o app le a primeira aba da planilha. Para escolher uma aba especifica, defina `GOOGLE_SHEET_WORKSHEET`.

## Variaveis de ambiente

Use `.env` localmente e configure as mesmas variaveis no EasyPanel:

```env
GOOGLE_SHEET_ID=15dKhTE2tJWXRlSCsrp4YafsnjWhpNhGuWgi3zJ-6xJE
GOOGLE_SHEET_WORKSHEET=
GOOGLE_SERVICE_ACCOUNT_JSON_BASE64=
```

Tambem e possivel usar um arquivo JSON local:

```env
GOOGLE_APPLICATION_CREDENTIALS=storage/sua-service-account.json
```

No EasyPanel, prefira `GOOGLE_SERVICE_ACCOUNT_JSON_BASE64`, porque evita montar arquivo de credencial no container.

## Instalar localmente

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Rodar o Streamlit

```powershell
.\.venv\Scripts\streamlit.exe run streamlit_app.py
```

O app abre em:

```text
http://localhost:8501
```

## Deploy no EasyPanel

1. Publique este projeto em um repositorio Git.
2. No EasyPanel, crie um novo servico do tipo `App`.
3. Em `Source`, aponte para o repositorio.
4. Use o `Dockerfile` da raiz.
5. Configure as variaveis de ambiente do `.env.example`.
6. Em `Domains`, direcione o dominio para a porta interna `8501`.
7. Clique em `Deploy`.

O container executa:

```text
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

## Funcionalidades

- leitura direta do Google Sheets;
- transformacao dos dados para colunas em portugues;
- cards de visao geral com total analisado, tempo medio de permanencia, idade media no desligamento e desligamentos por periodo;
- filtros por localizacao, area, senioridade, idade e salario;
- graficos por area e senioridade;
- tabela completa;
- download do CSV tratado.

## CLI legado

O script local com CSV foi mantido para compatibilidade:

```powershell
.\.venv\Scripts\python.exe scripts\transformar_theacellerator_gcp.py --sem-upload
```

Ele continua lendo `storage/theacellerator.csv` e gerando `storage/theacellerator_tratado.csv`.

## Seguranca

- Nao versionar `.env`.
- Nao versionar chaves JSON de service account.
- Nao versionar CSVs com dados sensiveis.
- No EasyPanel, cadastrar segredos apenas na area de variaveis de ambiente.
