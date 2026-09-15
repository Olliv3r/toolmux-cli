# Toolmux seed catalog

Este diretório contém o catálogo inicial de **500 candidatas** para curadoria no Toolmux. Os registros são pré-cadastros: permanecem com `publish=false` e situação experimental/aguardando até validação manual no Termux.

Cada registro procura antecipar o trabalho de cadastro com slug, nome, descrição de curadoria, autor/upstream, executável provável, homepage/repositório, método Git quando representável pelo contrato atual, dependências mínimas conhecidas, dica de instalação e metadados de revisão.

`author`, `executable` e descrições inferidas do upstream são **pré-preenchimento**, não confirmação de compatibilidade. Antes de mudar para Ativa, confirme o README atual, dependências, comando executável e comportamento no Termux.

## Validar

```bash
python -m toolmux_app.seed_tools --validate
```

## Filtrar

```bash
python -m toolmux_app.seed_tools --validate --category osint
python -m toolmux_app.seed_tools --validate --limit 100
```

## Importar no Web

```bash
flask seed-tools /caminho/toolmux-cli/seeds/tools --dry-run
flask seed-tools /caminho/toolmux-cli/seeds/tools
```

O importador é idempotente. O `slug` é a identidade lógica e é mapeado para o alias da ferramenta no Web.

## Curadoria

1. Abra a candidata no painel.
2. Confira upstream, descrição, executável, dependências e instalação.
3. Teste no Termux.
4. Corrija somente o necessário.
5. Altere a situação para Ativa quando aprovada.

Não adicione tokens, `.env`, credenciais ou comandos remotos arbitrários aos datasets.
