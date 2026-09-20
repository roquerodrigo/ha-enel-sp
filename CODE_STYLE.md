# Guia de estilo de código

Convenções de estilo do projeto `ha-enel-sp`. Antes de commitar, execute
`uv run ruff format --check .`, `uv run ruff check .` e
`uv run mypy custom_components/enel_sp` — todos devem terminar sem erros.
Em seguida vem `uv run pytest` (com o gate de 90 % de cobertura).

**Sempre leia este arquivo antes de adicionar ou reestruturar código.**

## Idioma

`hacs.json` declara `"country": ["BR"]`: a integração só faz sentido no Brasil,
portanto o português do Brasil é o idioma do repositório.

- **Tudo que é prosa lida por pessoas fica em pt-BR:**
  - Documentação: `README.md`, `CONTRIBUTING.md`, este guia, `CLAUDE.md`, os
    demais arquivos Markdown, docstrings e comentários de código.
  - Histórico do Git: assunto e corpo dos commits, títulos e descrições de PR.
  - Releases: notas de release e `CHANGELOG.md`, inclusive os títulos de seção
    (`changelog-sections` em `release-please-config.json`).
  - Comunicação pública: issues, comentários em issues e PRs, reviews, e os
    templates de issue e de PR em `.github/`.
  - Metadados: a descrição do repositório no GitHub e `description` em
    `pyproject.toml`.
- **O código permanece em inglês:** nomes de arquivo, de classe, de função e de
  variável, chaves de dicionário, strings identificadoras, nomes de branch e
  mensagens de log. Tudo que uma ferramenta interpreta também é código: o tipo
  e o escopo do Conventional Commit
  (`feat(sensor): adiciona a bandeira tarifária`), o rodapé `BREAKING CHANGE:`,
  ids de workflow e de job, labels.
- **Termos nativos do domínio nunca são traduzidos**, nem no código nem na
  prosa. Eles são a linguagem ubíqua compartilhada com os usuários e com o
  portal: escreva `bandeira_tarifaria`, `unidade_consumidora`, `segunda_via`,
  e não `tariff_flag`, `consumer_unit`, `duplicate_bill`. O que envolve o termo
  continua em inglês (`fetch_bandeira_tarifaria`). Identificadores perdem os
  acentos (`instalacao`); a prosa e as strings traduzidas os mantêm
  (`instalação`).
- O idioma da conversa com o usuário nunca decide o que vai para o disco.
- As strings exibidas ao usuário ficam somente em
  `custom_components/enel_sp/translations/{en,pt-BR}.json` — nunca fixas no
  Python. `en.json` continua obrigatório ao lado do locale do país.

## Organização dos arquivos

- **Uma classe de nível superior por arquivo — incluindo TypedDicts e
  dataclasses.** Várias classes semanticamente relacionadas (famílias de
  exceções, entidades de sensor de uma plataforma, os payloads tipados e os
  dados de runtime) são agrupadas em um diretório de pacote, com uma classe por
  submódulo e um `__init__.py` que reexporta os símbolos públicos.
  - Exemplo: `exceptions/` contém `api_client_error.py`,
    `api_client_communication_error.py`, `api_client_authentication_error.py`,
    além de `__init__.py`.
  - Exemplo: `data/` contém `post.py`, `config_data.py`, `options_data.py`,
    `diagnostics_entry.py`, `diagnostics_payload.py`, `runtime.py`, além de um
    `__init__.py`. Cada TypedDict e cada dataclass tem o próprio arquivo — um
    `data.py` plano com várias classes é dívida de migração, não um layout
    válido.
  - **Flexibilizações**: um TypedDict ou alias `type` consumido por um único
    módulo pode viver nesse módulo em vez de ter arquivo próprio, e dataclasses
    folha que descrevem fragmentos do mesmo payload podem dividir um módulo. O
    layout de pacote com uma classe por submódulo volta a ser o padrão assim
    que um formato é compartilhado entre módulos.
- **Aliases `type` são a exceção: ficam em `data/__init__.py`**, junto das
  reexportações (`JsonPrimitive`, `JsonValue`, `JsonObject`,
  `EnelSpConfigEntry`), e não em arquivos próprios.
- **Funções auxiliares** podem ficar no mesmo arquivo da única classe que as
  usa (ex.: `_verify_response_or_raise` em `api.py`).
- **O `__init__.py` do pacote da integração** liga `async_setup_entry`,
  `async_unload_entry`, `async_reload_entry` e nada mais.

## Entidades: uma classe por entidade

- **Uma classe por entidade.** Toda entidade tem a própria classe dedicada —
  nunca compartilhe uma classe genérica parametrizada por uma subclasse de
  `EntityDescription` com campos chamáveis como `value_fn` ou `action_fn`.
  Codifique o comportamento da entidade diretamente na classe, por meio de
  `@property` e de constantes `_attr_*` em nível de classe (ou de uma instância
  simples de `EntityDescription` atribuída em nível de classe).
  - Não escreva uma subclasse `<DOMAIN><Platform>Description` com um campo
    `value_fn` / `action_fn`.
  - Escreva `<DOMAIN><Name><Platform>` (ex.: `EnelSpStatusSensor`,
    `EnelSpCancelButton`, `EnelSpDoorBinarySensor`).
- O motivo: cada entidade é um contrato discreto; misturá-las em uma classe
  genérica esconde o contrato atrás de indireção e desestimula o refinamento
  por entidade (ícones, atributos de estado, lógica própria).
- **Os ícones das entidades ficam em `icons.json`**
  (`entity.<platform>.<translation_key>.default`), indexados pela
  `translation_key` da entidade — não em `_attr_icon`. O arquivo de ícones
  aceita variantes por estado e por faixa e mantém a apresentação fora do
  Python.

## Nomenclatura

- Classes públicas têm o prefixo `EnelSp`.
- Entidades concretas de plataforma terminam com o tipo da entidade:
  `EnelSpSensor`, `EnelSpBinarySensor`,
  `EnelSpSwitch`.
- Classes de exceção terminam com `Error`: `EnelSpApiClientError`,
  `…CommunicationError`, `…AuthenticationError`.
- Atributos e funções privados têm o prefixo `_`.

## Tipagem

**Tipagem estrita. Sem genéricos, sem `Any`.** O mypy (`uv run mypy custom_components/enel_sp`) garante isso.

Proibidos: `typing.Any`, `object` como tipo de valor, `dict` / `list` / `tuple` /
`set` sem parâmetros, `dict[str, Any]`, `Mapping[str, Any]`.

Obrigatórios:

- `TypedDict` para formatos conhecidos de dict / JSON (veja o pacote `data/`
  para os exemplos canônicos: `EnelSpPost`, `EnelSpConfigData`,
  `EnelSpOptionsData`, `EnelSpDiagnosticsPayload`,
  um por arquivo).
- `@dataclass` para registros estruturados (`EnelSpData` em
  `data/runtime.py`).
- Aliases `type` nomeados para formatos recursivos / compartilhados —
  `JsonPrimitive`, `JsonValue`, `JsonObject` em `data/__init__.py`.
- `frozenset[str]` / `tuple[str, ...]` para coleções fixas de strings.
- `cast("TypedDictName", value)` nas fronteiras com o framework do HA que nos
  entregam um tipo permissivo (ex.: `entry.data` é
  `MappingProxyType[str, Any]`).

Ao estreitar a assinatura de um callback fornecido pelo HA (ex.:
`async_step_user`), o mypy reporta `[override]` (violação de Liskov). Adicione
`# type: ignore[override]` com um comentário de uma linha explicando o
estreitamento deliberado — veja `config_flow.py` para o exemplo canônico.

## Propriedades e `__init__`

- **Sempre prefira `@property`** a atribuir valores `_attr_*` no `__init__`.
  As propriedades são calculadas sob demanda a partir dos campos guardados na
  classe pai (ex.: `self.coordinator`, `self.entity_description`).
- Quando o corpo do `__init__` só chamaria `super().__init__(...)`, omita o
  `__init__` por completo e deixe o Python herdar o da classe pai.
- Constantes em nível de classe como `_attr_attribution = ATTRIBUTION` e
  `_attr_has_entity_name = True` são aceitáveis — não dependem do estado da
  instância.

## Imports

- Sempre comece todo módulo com `from __future__ import annotations`, para que
  as anotações de tipo virem strings avaliadas sob demanda e o custo em runtime
  dos imports sob `if TYPE_CHECKING` seja zero.
- Imports relativos dentro do mesmo pacote (`from .module import …`) são o
  padrão.
- Mova os imports usados apenas em tipos para um bloco `TYPE_CHECKING` (Ruff
  `TC001`/`TC003`):

  ```python
  from __future__ import annotations
  from typing import TYPE_CHECKING

  if TYPE_CHECKING:
      from collections.abc import Mapping
      from .data import EnelSpConfigData
  ```

- Comentários `noqa` são reservados a restrições inevitáveis do framework (ex.:
  `# noqa: ARG001` para parâmetros de callback do HA que precisam existir mas
  não são usados). Documente o motivo na própria linha quando não for óbvio.
  Nunca silencie uma regra para "agradar o ruff" — corrija o código.

## Docstrings

- Toda classe, função e método públicos (incluindo `@property`) e todo
  `__init__` têm docstring. O Ruff garante isso com `D102`/`D107`.
- Uma única frase costuma bastar. Descreva o *contrato* ou o *porquê*, não a
  implementação óbvia.
- Docstring de módulo no topo de todo arquivo `.py`.
- Evite repetir o tipo — a assinatura já faz isso.
- As docstrings são escritas em pt-BR (veja "Idioma").

## Comentários

- O padrão é **nenhum comentário**. Adicione um somente quando o *porquê* não
  for óbvio pelo código: uma restrição oculta, um contorno, uma invariante
  sutil ou uma sobreposição deliberada do sistema de tipos.
- Nunca descreva *o que* o código faz — identificadores bem nomeados cuidam
  disso.
- **Nada de divisores de seção** como `# --- API payloads ---` para agrupar
  declarações relacionadas. Se um arquivo tem tantas seções que você sente
  falta de separadores visuais, divida-o em vários arquivos.

## Logging

- Cada módulo usa o `LOGGER` do pacote, definido em `const.py`
  (`LOGGER: Logger = getLogger(__package__)`); nunca chame
  `logging.getLogger(...)` de forma avulsa.
- As mensagens de log são escritas em inglês (veja "Idioma").
- Use **formatação `%` preguiçosa**, nunca f-strings — elas forçam a
  interpolação mesmo quando o nível está filtrado:

  ```python
  LOGGER.warning("Refresh failed: %s", exception)   # ✓
  LOGGER.warning(f"Refresh failed: {exception}")    # ✗
  ```

- Níveis:
  - `debug` — resumos de buscas bem-sucedidas, diagnósticos de cada poll.
  - `info` — eventos únicos do ciclo de vida (setup concluído, fluxo de reauth
    iniciado).
  - `warning` — falhas recuperáveis (erro transitório da API, uso de fallback).
  - `error` / `exception` — irrecuperável no ciclo atual; use `exception` com
    exceções capturadas dentro de blocos `except` para ter o traceback
    completo.
- Nunca registre segredos (`token`, `password`, `key`, cabeçalhos completos). O
  mapeamento `Coordinator → UpdateFailed` deve descartar a forma textual da
  exceção original quando ela puder expô-los.

## Mensagens de erro

- Formato: `"Failed to <verb> <object>: <cause>"`, em que `<cause>` é a exceção
  ou um motivo curto. Mantenha-as curtas e fáceis de achar com grep.
- Valide as entradas antes da chamada de rede, para que os erros exibidos ao
  usuário apontem para a entrada incorreta e não para um traceback posterior
  (`config_flow._validate` rejeita credenciais malformadas antes de contatar a
  API).
- As exceções próprias seguem a mesma hierarquia:
  `EnelSpApiClientError` (base) → `…CommunicationError` (timeout, conexão, DNS)
  e `…AuthenticationError` (401/403). Encapsule os erros brutos do upstream na
  fronteira do cliente da API; tudo acima só captura a hierarquia própria.

## Coordinator e dados de runtime

- Todo o estado da API passa por `entry.runtime_data: EnelSpData`
  (`data/runtime.py`). Nunca guarde estado da integração em `hass.data` —
  `runtime_data` é descartado automaticamente no unload, e o padrão legado
  `hass.data[DOMAIN][entry_id]` não é.
- O coordinator é tipado como `DataUpdateCoordinator[EnelSpPost]`
  (ou o TypedDict que for o seu payload real). `_async_update_data` retorna o
  payload tipado.
- Use `await coordinator.async_config_entry_first_refresh()` durante
  `async_setup_entry` (não `async_refresh()`) — uma primeira atualização que
  falha levanta `ConfigEntryNotReady`, e o HA tenta de novo com backoff
  automaticamente.
- Passe `always_update=False` ao coordinator quando o TypedDict do payload
  puder ser comparado de forma limpa com `__eq__`; o HA então deixa de chamar
  os listeners e de gravar estado quando os dados não mudaram.
- Use `self.async_contexts()` dentro de `_async_update_data` para restringir o
  trabalho na API às entidades atualmente inscritas — entidades desabilitadas
  não devem gerar chamadas de rede.
- Mapeamento de erros dentro de `_async_update_data`:
  - Erros de comunicação → `raise UpdateFailed("Failed to …: %s" % err)`. Passe
    `retry_after=<seconds>` quando o upstream sinalizar um backoff explícito
    (ex.: `Retry-After` de um HTTP 429).
  - Erros de autenticação → `raise ConfigEntryAuthFailed(...)` — o HA cancela
    as próximas atualizações e inicia o fluxo `SOURCE_REAUTH`.
  - Nunca deixe strings brutas de exceções do upstream chegarem a
    `UpdateFailed` quando puderem carregar tokens; converta para uma mensagem
    sanitizada no cliente da API.

## Config / options / repairs / diagnostics

- `config_flow.py` contém os passos `user`, `reauth`, `reauth_confirm` e
  `reconfigure`, todos compartilhando um único helper `_validate` e um único
  construtor `_credentials_schema`.
- `options_flow.py` contém a única classe `EnelSpOptionsFlow`. Novas chaves de
  opções entram no TypedDict `EnelSpOptionsData`, em `data/options_data.py`.
- `repairs.py` expõe `async_create_fix_flow`. Helpers de exemplo como
  `async_raise_deprecated_api_issue` mostram como registrar issues a partir de
  qualquer ponto da integração.
- `diagnostics.py` retorna `EnelSpDiagnosticsPayload`. As chaves sensíveis
  entram na constante `TO_REDACT: frozenset[str]`.

## Traduções

- Dois locales: `en.json` e `pt-BR.json`. `tests/test_translations.py`
  parametriza todos os locales e falha se os conjuntos de chaves aninhadas
  divergirem.
- As strings de issues ficam em `issues.<issue_id>`; as de opções, em
  `options.step.init.data`; as de fluxo, em `config.step.<step_id>`; os nomes
  das entidades, em `entity.<platform>.<key>.name`.

## Requisitos de publicação no HACS

O [HACS](https://www.hacs.xyz/docs/publish/integration/) valida o formato do
repositório a cada push por meio de `hacs/action@main` (e o próprio HA executa o
`hassfest`). Os dois gates precisam permanecer verdes:

- **Uma integração por repositório**, localizada em
  `custom_components/<domain>/`.
- `manifest.json` deve declarar `domain`, `name`, `version`, `documentation`,
  `issue_tracker`, `codeowners`. A chave `version` é **obrigatória para
  integrações custom** (omita-a apenas em integrações do core) e precisa ser
  interpretável como `AwesomeVersion` — CalVer ou SemVer.
- `manifest.json` também declara `integration_type`. JSON não aceita
  comentários, então a escolha fica registrada aqui: esta integração usa `hub`
  porque uma config entry representa uma conta de cliente que expõe um
  dispositivo por instalação.
- `hacs.json`, na raiz do repositório, fixa a versão mínima do core do HA pela
  chave `homeassistant`. Este é o terceiro pin do HA (veja `CLAUDE.md`).
- `hacs.json` declara `"country": ["BR"]` (ISO 3166-1 alpha-2). Um usuário do
  HACS que configura outro país deixa de ver este repositório na loja; a
  Enel São Paulo só atende o Brasil, e é essa chave que define o idioma do
  repositório (veja "Idioma").
- Os assets de marca ficam em `custom_components/<domain>/brand/` — `icon.png`,
  `logo.png` (+ variantes `@2x`). O Home Assistant 2026.3+ serve esse diretório
  diretamente da integração, antes do CDN do
  [home-assistant/brands](https://github.com/home-assistant/brands), portanto
  nenhuma submissão ao brands é necessária; `brand/README.md` registra a origem
  e como os arquivos foram produzidos.
- Um `README.md` na raiz do repositório é obrigatório; o HACS o exibe como a
  descrição da integração. O cabeçalho dele segue o layout abaixo.

O release-please cria a tag de release a cada merge na `main`; o HACS mostra
aos usuários as cinco releases mais recentes do GitHub, então mantenha o
changelog fácil de pesquisar.

## Cabeçalho do README

Todo repositório abre o `README.md` com o mesmo cabeçalho, exatamente nesta
ordem: **título → badges → link do HACS → separador `---` → o restante do
documento.**

```markdown
# <Title>

[![CI](https://github.com/roquerodrigo/<repo>/actions/workflows/ci.yml/badge.svg)](https://github.com/roquerodrigo/<repo>/actions/workflows/ci.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open the repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roquerodrigo&repository=<repo>&category=integration)

---
```

- `owner=` é sempre `roquerodrigo`; `repository=` é o nome do repositório.
- `category=integration` para uma integração; `category=plugin` para um
  repositório de card Lovelace.
- O link do HACS é um parágrafo próprio, separado do bloco de badges por uma
  linha em branco. A linha de badges e o botão "Open your Home Assistant
  instance" são coisas diferentes e não devem ficar juntos.
- Preserve os badges que o repositório já tem e não invente novos; todos ficam
  **antes** do link do HACS.
- O `---` imediatamente após o link do HACS é o separador do cabeçalho. Um
  README que já usa `---` mais abaixo mantém esses como quebras de seção — não
  adicione um segundo separador ao cabeçalho.

**Um repositório privado não recebe o link do HACS.** O `my.home-assistant.io`
resolve o destino pela API pública do GitHub, então em um repositório privado o
botão leva a algo que o HACS não consegue instalar. É o mesmo motivo pelo qual
esses repositórios chamam o workflow de validação com `hacs: false`. Publique o
título, os badges e o separador, e adicione o link quando — e somente quando —
o repositório se tornar público.

## Quality scale

- `quality_scale.yaml` é **opcional**, e este repositório não tem um. Ele só é
  exigido quando `manifest.json` declara um nível de `quality_scale` — e, nesse
  caso, toda afirmação nele precisa ser honesta (`done` somente quando a regra
  está de fato implementada; use `todo`/`exempt` nos demais casos).
- O objetivo é aplicar as [regras Bronze/Silver/Gold](https://developers.home-assistant.io/docs/core/integration-quality-scale/)
  que forem pertinentes à integração; Platinum é uma aspiração, não um gate de
  revisão.

## Hooks de pre-commit

O `pre-commit` é uma dependência de desenvolvimento (`pyproject.toml`), e o
`.pre-commit-config.yaml` executa ruff format, ruff check e mypy como **hooks
locais por meio de `uv run`**, de modo que todo commit usa exatamente as versões
das ferramentas fixadas em `pyproject.toml`/`uv.lock` — as mesmas que o CI
resolve. Nunca troque esses hooks por versões espelhadas (`ruff-pre-commit`,
`mirrors-mypy`): um hook espelhado carrega o próprio pin de versão, que se
afasta silenciosamente do pin do projeto. Instale uma vez por clone:

```bash
pre-commit install
```

O hook executa, a cada commit, os mesmos gates de lint do CI. Só o ignore em um
`git commit --no-verify` de emergência, e reexecute imediatamente
`scripts/lint` (ou os comandos diretos equivalentes).

## Conventional commits

Todos os commits seguem o [Conventional Commits](https://www.conventionalcommits.org/),
que o `release-please` interpreta para incrementar a versão e gerar o
`CHANGELOG.md`:

| Tipo | Significado | Incremento |
|---|---|---|
| `feat` | Nova funcionalidade | minor |
| `fix` | Correção de bug | patch |
| `perf` | Melhoria de desempenho | patch |
| `deps` | Atualização de dependência | patch |
| `docs` | Somente documentação | nenhum |
| `refactor` | Refatoração sem mudança de comportamento | nenhum |
| `test` | Mudança apenas em testes | nenhum |
| `ci` | Mudança de CI / ferramentas | nenhum |
| `chore` | Qualquer outra coisa (raro) | nenhum |

- Assunto: modo imperativo, em minúsculas, sem ponto final, **em pt-BR**. O
  tipo e o escopo permanecem em inglês, porque é deles que o `release-please`
  deriva a versão.
- Use escopos quando forem úteis:
  `fix(sensor): mapeia valores de interface fora do enum para None`.
- Um rodapé `BREAKING CHANGE:` (ou `!` após o tipo) incrementa a versão major.

## Lint e verificação

- A configuração do Ruff fica em `pyproject.toml` (`[tool.ruff]`), com `select = ["ALL"]`.
- A configuração do mypy fica em `pyproject.toml` (`[tool.mypy]`). Execute os
  dois com `uv run ruff check .` e `uv run mypy custom_components/enel_sp`.
- Após cada mudança, execute `uv run ruff format --check .`,
  `uv run ruff check .`, `uv run mypy custom_components/enel_sp` e
  `uv run pytest`. Os dois gates espelham o CI. `scripts/lint` é um wrapper
  fino que apenas encadeia esses quatro comandos — executá-lo ou executar os
  comandos diretamente é equivalente; o wrapper existe para que CI,
  documentação e hábitos locais compartilhem uma única fonte da verdade.
- Os testes ficam em `tests/`, espelhando o layout de produção. O gate de 90 %
  de cobertura (`pyproject.toml`, `[tool.pytest.ini_options]`) impede que código
  sem teste entre. Quando um teste exercita um estado impossível sob os novos
  tipos, atualize-o ou remova-o — nunca enfraqueça o tipo para satisfazer o
  teste.
