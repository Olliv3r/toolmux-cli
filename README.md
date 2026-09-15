# Toolmux CLI

Toolmux CLI é uma interface de terminal para descobrir, consultar e
instalar ferramentas disponibilizadas pelo catálogo oficial do Toolmux.

O projeto foi pensado para ambientes Linux e Termux, oferecendo uma
experiência simples no terminal enquanto mantém os dados das ferramentas
centralizados em uma API. O CLI não mantém um catálogo próprio como
fonte de verdade: nomes, categorias, métodos de instalação, dependências
e demais metadados são fornecidos pelo serviço Toolmux.

## Visão geral

O Toolmux separa a interface de terminal do gerenciamento do catálogo.

``` text
┌──────────────────┐
│   Toolmux API    │
│ catálogo oficial │
└────────┬─────────┘
         │ HTTPS / JSON
         ▼
┌──────────────────┐
│   Toolmux CLI    │
│ busca/instalação │
└────────┬─────────┘
         │
         ▼
     apt / git
```

Essa arquitetura permite atualizar o catálogo sem precisar publicar uma
nova versão do CLI sempre que uma ferramenta é adicionada ou seus dados
são alterados.

Quando a API está disponível, o CLI consulta o catálogo remoto e
trabalha com os dados mais recentes. O cache local permite continuidade
de consulta quando o serviço fica temporariamente indisponível.

## Recursos

-   Catálogo de ferramentas fornecido pela API Toolmux.
-   Busca e navegação por ferramentas e categorias.
-   Instalação por **APT** e **Git**.
-   Resolução das dependências definidas no catálogo.
-   Cache local para indisponibilidades temporárias da API.
-   Validação do contrato da API antes de consumir o catálogo.
-   Atualização do catálogo sem necessidade de atualizar o pacote do
    CLI.
-   Sistema integrado de reporte de problemas.
-   Informações sobre origem e método de instalação.

## Relação com a API

A API é a fonte de verdade do Toolmux.

O CLI consome um contrato versionado e valida a resposta antes de
utilizá-la. Isso reduz o risco de uma alteração incompatível no servidor
provocar instalações incorretas ou comportamento inesperado no cliente.

Entre os dados recebidos estão:

-   identificação e descrição da ferramenta;
-   categorias;
-   situação de publicação;
-   executável esperado;
-   método de instalação;
-   pacote APT, quando aplicável;
-   repositório Git, quando aplicável;
-   dependências necessárias;
-   instruções informativas de instalação.

### APT

Para instalações APT, o catálogo informa explicitamente o nome do
pacote. O alias ou nome visual da ferramenta não são usados como
substitutos do pacote.

``` text
Toolmux API
    ├── type: apt
    └── package_name
             │
             ▼
        Toolmux CLI
             │
             ▼
        apt install
```

### Git

Para instalações Git, a API fornece os dados do repositório e as
dependências necessárias.

``` text
Toolmux API
    ├── type: git
    ├── repository
    └── dependencies
             │
             ▼
        Toolmux CLI
             │
             ▼
        clone / update
```

O CLI não executa comandos arbitrários enviados pelo catálogo. As ações
seguem os métodos suportados pelo próprio cliente.

## Cache e modo offline

O catálogo remoto é priorizado sempre que a API está acessível.

O CLI pode utilizar uma cópia previamente validada do catálogo durante
uma indisponibilidade temporária do serviço. O cache não é uma segunda
base de dados e não substitui a API como fonte oficial.

Quando uma nova resposta válida é recebida, os dados locais são
atualizados de acordo com o catálogo publicado.

## Instalação

Clone o repositório:

``` bash
git clone <URL-DO-REPOSITORIO>
cd toolmux-cli
```

Opcionalmente, crie um ambiente virtual:

``` bash
python -m venv .venv
source .venv/bin/activate
```

Instale as dependências:

``` bash
pip install -r requirements.txt
```

Depois execute o Toolmux conforme o entry point disponibilizado pelo
projeto.

> O endereço do serviço e as credenciais de acesso não são armazenados
> no repositório público. A configuração local deve permanecer fora do
> controle de versão.

## Configuração

O Toolmux CLI possui uma pequena configuração local para se comunicar
com a API.

Por segurança, arquivos `.env`, tokens e configurações específicas de
desenvolvimento ou produção **não devem ser versionados**. Credenciais
também não devem aparecer em issues, commits, screenshots ou logs
públicos.

## Reporte de problemas

O CLI possui integração com o sistema de reporte do Toolmux.

Os relatórios são enviados para a API, que fica responsável pelo
processamento e encaminhamento. O cliente não precisa conhecer os
serviços internos utilizados pelo backend para receber ou notificar
esses relatórios.

Esse desenho mantém integrações e credenciais privadas fora do projeto
público.

Ao reportar um problema, forneça uma descrição objetiva e, quando
possível, informações suficientes para reproduzi-lo. Antes de publicar
logs, verifique se não contêm tokens ou outros dados sensíveis.

## Desenvolvimento

Para executar os testes:

``` bash
pytest
```

A suíte cobre pontos como validação do contrato do catálogo,
autenticação das requisições, configuração, cache, instalações APT/Git,
dependências e sistema de reporte.

Alterações que afetem o formato do catálogo devem preservar a
compatibilidade com a versão de contrato suportada pelo CLI ou ser
acompanhadas de uma atualização explícita do contrato.

## Princípios do projeto

1.  **A API é a fonte de verdade.** O CLI não mantém um catálogo
    independente.
2.  **Instalações são explícitas.** O cliente não deve adivinhar nomes
    de pacotes ou métodos.
3.  **O contrato é versionado.** Incompatibilidades entre API e CLI
    devem ser detectáveis.
4.  **Segredos ficam fora do código.** Tokens e configurações privadas
    não pertencem ao repositório público.
5.  **O backend permanece desacoplado.** O CLI não precisa conhecer
    painel Web, banco ou serviços internos.
6.  **Cache não é catálogo.** O cache existe para resiliência, não como
    segunda fonte oficial.

## Segurança

Não faça commit de arquivos `.env`, tokens, credenciais, caches locais
ou logs contendo informações sensíveis.

Caso uma credencial seja publicada acidentalmente, considere-a
comprometida e substitua-a no serviço correspondente.

## Status

O Toolmux está em desenvolvimento ativo. O catálogo, a interface de
terminal e os fluxos de instalação podem evoluir conforme novos casos de
uso forem incorporados.

Contribuições, testes em diferentes ambientes e relatos de problemas
ajudam a melhorar a compatibilidade e a experiência do CLI.

## Licença

Consulte o arquivo de licença do repositório para conhecer os termos
aplicáveis ao projeto.
