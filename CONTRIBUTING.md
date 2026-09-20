# Diretrizes de contribuição

Contribuir com este projeto deve ser o mais fácil e transparente possível, seja para:

- Reportar um bug
- Discutir o estado atual do código
- Enviar uma correção
- Propor novas funcionalidades

## O GitHub é usado para tudo

O GitHub hospeda o código, acompanha issues e pedidos de funcionalidade e recebe os pull requests.

Pull requests são a melhor forma de propor mudanças no código.

1. Faça um fork do repositório e crie a sua branch a partir da `main`.
2. Se você alterou algo, atualize a documentação.
3. Garanta que o código passa no lint (execute `uv run ruff format --check .`, `uv run ruff check .` e `uv run mypy custom_components/enel_sp`).
4. Teste a sua contribuição.
5. Abra o pull request!

## Idioma

Este repositório declara `"country": ["BR"]` em `hacs.json`, portanto documentação, comentários, mensagens de commit, pull requests e issues são escritos em português do Brasil. O código permanece em inglês, assim como o tipo e o escopo do Conventional Commit (`fix(sensor): corrige o vencimento da conta`). Os termos nativos do domínio nunca são traduzidos. Veja a seção "Idioma" do [`CODE_STYLE.md`](./CODE_STYLE.md).

## Toda contribuição fica sob a licença MIT

Em resumo, ao enviar mudanças de código, entende-se que elas ficam sob a mesma [licença MIT](http://choosealicense.com/licenses/mit/) que cobre o projeto. Entre em contato com os mantenedores se isso for um problema.

## Reporte bugs pelas [issues](../../issues) do GitHub

As issues do GitHub são usadas para acompanhar os bugs públicos.
Reporte um bug [abrindo uma nova issue](../../issues/new/choose); é simples assim!

## Escreva relatos de bug com detalhes, contexto e código de exemplo

**Bons relatos de bug** costumam ter:

- Um resumo rápido e/ou contexto
- Passos para reproduzir
  - Seja específico!
  - Forneça código de exemplo, se puder.
- O que você esperava que acontecesse
- O que acontece de fato
- Observações (possivelmente incluindo por que você acha que isso acontece, ou o que você tentou e não funcionou)

## Use um estilo de código consistente

O projeto usa o [ruff](https://docs.astral.sh/ruff/) (configuração em `pyproject.toml`). Execute `uv run ruff format --check .`, `uv run ruff check .` e `uv run mypy custom_components/enel_sp` antes de enviar um PR.

## Teste a sua modificação

Este projeto é baseado no [ha-integration-blueprint](https://github.com/roquerodrigo/ha-integration-blueprint).

Execute `scripts/setup` uma vez para criar o ambiente virtual gerenciado pelo `uv` e, em seguida, `scripts/develop` para iniciar uma instância isolada do Home Assistant em modo debug, com a integração carregada e o arquivo [`configuration.yaml`](./config/configuration.yaml) incluído.

## Licença

Ao contribuir, você concorda que as suas contribuições serão licenciadas sob a licença MIT do projeto.
