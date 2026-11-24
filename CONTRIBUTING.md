# Contribuindo

Relatos de bug, ideias e pull requests são bem-vindos.

## Relatando um bug

Abra uma [issue](https://github.com/roquerodrigo/ha-enel-sp/issues/new/choose)
com:

- a versão do Home Assistant e a da integração;
- o que você fez, o que esperava e o que aconteceu;
- os diagnósticos baixados na página da integração (o login, a senha e os
  dados pessoais são removidos) e as linhas relevantes do log.

## Ambiente de desenvolvimento

O projeto usa o [uv](https://docs.astral.sh/uv/), que cria e gerencia o
`.venv` sozinho.

```bash
scripts/setup      # instala as dependências no .venv
scripts/develop    # inicia o Home Assistant em http://localhost:8123 com a integração carregada
```

O `scripts/develop` usa a configuração em [`config/`](config/), com o log da
integração em nível debug.

Para testar na mesma versão do Home Assistant usada pelos testes, o
[`compose.yaml`](compose.yaml) roda o container oficial na porta 8124, com a
sua árvore de trabalho montada como somente leitura:

```bash
docker compose up -d        # inicia em http://localhost:8124
docker compose logs -f      # acompanha o log
docker compose restart      # recarrega a integração depois de uma mudança
docker compose down         # para, mantendo o config/
```

Os dois usam o mesmo `config/`, então não rode os dois ao mesmo tempo.

## Verificações

Rode estes comandos antes de abrir um pull request. O CI roda os mesmos, e o
`scripts/lint` encadeia os quatro.

```bash
uv run ruff format --check .             # formatação
uv run ruff check .                      # lint
uv run mypy custom_components/enel_sp    # tipos
uv run pytest                            # testes, a cobertura precisa ficar em 90 % ou mais
```

Com `pre-commit install`, o ruff format, o ruff check e o mypy rodam a cada
commit.

Leia o [CODE_STYLE.md](CODE_STYLE.md) antes de criar ou reorganizar código.

## Pull requests

1. Faça um fork do repositório e crie a sua branch a partir da `main`.
2. Escreva as mensagens de commit no
   [Conventional Commits](https://www.conventionalcommits.org/), com o assunto
   em português: `fix(sensor): corrige o vencimento da conta`. As releases e as
   notas delas são geradas a partir dos commits. Marque mudanças que quebram a
   compatibilidade com `!` ou com o rodapé `BREAKING CHANGE:`.
3. Atualize `translations/en.json` e `translations/pt-BR.json` juntos quando
   mudar textos exibidos ao usuário.
4. Atualize o README quando o comportamento, a configuração ou as entidades
   mudarem.
5. Preencha o template do pull request.

## Idioma

Como o `hacs.json` declara `"country": ["BR"]`, a documentação, os
comentários, as mensagens de commit, os pull requests e as issues são em
português do Brasil. O código fica em inglês, assim como o tipo e o escopo do
commit. Os termos do domínio, como `bandeira_tarifaria` e
`unidade_consumidora`, nunca são traduzidos. A regra completa está na seção
"Idioma" do [CODE_STYLE.md](CODE_STYLE.md).

## Licença

As contribuições são publicadas sob a [licença MIT](LICENSE) do projeto.
