# Toolmux CLI

Instalador de ferramentas para Termux/Android e consumidor do catálogo publicado pelo Toolmux Web.

## Instalação

```bash
apt update
apt upgrade
apt install python git -y
git clone https://github.com/Olliv3r/toolmux-cli ~/toolmux-cli
cd ~/toolmux-cli
pip install -r requirements.txt
./toolmux.py
```

## Contrato com o Web

A versão atual do CLI consome `contract_version: "2.0"` / `schema_version: 2` em `GET /api/v1/catalog`.

O Web fornece explicitamente os dados necessários para instalar:

- `alias`: somente identificador do Toolmux;
- `executable`: comando esperado após instalação;
- APT: `package_name` obrigatório;
- Git: `repository.name` e `repository.url` obrigatórios;
- `dependencies[].package_name`: pacotes instalados antes da ferramenta;
- `tip`: texto informativo, nunca executado automaticamente.

O instalador **não usa mais `alias` como nome do pacote APT** e não suporta `dpkg`.

A API Web é a fonte de verdade. Falhas de API/contrato são exibidas ao usuário e não são mascaradas por banco legado. O cache local validado por ETag é usado normalmente em respostas HTTP 304; fallback offline só é permitido quando `TOOLMUX_ALLOW_OFFLINE_CACHE=1`.

## Configuração por `.env`

O CLI carrega automaticamente `.env` sem sobrescrever variáveis já exportadas no shell. O pacote de desenvolvimento vem apontando para a API Flask local:

```dotenv
TOOLMUX_API_BASE_URL=http://127.0.0.1:5000/api/v1
TOOLMUX_API_TOKEN=toolmux-local-dev-token
TOOLMUX_ALLOW_OFFLINE_CACHE=0
```

No Web local, configure **o mesmo** `TOOLMUX_API_TOKEN`. Esse token é um segredo compartilhado do Toolmux usado no header `Authorization: Bearer ...`; ele não é fornecido pelo Termux e não tem relação com o app/add-on Termux:API.

Variáveis exportadas no Termux têm precedência sobre `.env`:

```bash
export TOOLMUX_API_BASE_URL='https://seu-host/api/v1'
export TOOLMUX_API_TOKEN='o-token-configurado-no-web'
# Compatibilidade com versões anteriores:
# export TOOLMUX_API_PASSWORD='token-legado'
```

Também é possível apontar para outro arquivo com `TOOLMUX_ENV_FILE=/caminho/toolmux.env`.

## Segurança de execução

Comandos externos usam listas de argumentos com `subprocess.run(..., check=True)`, sem `shell=True`. Dependências são pacotes explícitos do contrato. `installation_tip` é apenas mostrado ao usuário.

## Desenvolvimento

```bash
pip install -e '.[dev]'
PYTHONPATH=. pytest -q
```

## Licença

MIT. Consulte `LICENSE`.


## Contrato com o Web

Veja `CONTRACT.md` e `CONTRACT_AUDIT.md` para as invariantes de instalação e compatibilidade.
