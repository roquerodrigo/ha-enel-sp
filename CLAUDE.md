# CLAUDE.md

Orientações para agentes do Claude Code (claude.ai/code) que trabalham neste repositório.

## Sempre leia o `CODE_STYLE.md` primeiro

Antes de criar, renomear ou reestruturar qualquer arquivo/classe/função, **leia o [`CODE_STYLE.md`](./CODE_STYLE.md)**. Ele é a única fonte da verdade para as convenções: idioma, organização dos arquivos, nomenclatura, tipagem, propriedades vs `__init__`, imports, docstrings, comentários, padrão do coordinator, layout de repairs/diagnostics, traduções, fluxo de lint.

Para os tópicos voltados ao usuário (entidades, instalação, como o portal é acionado, diagrama do layout, comandos úteis, lista do CI), veja o [`README.md`](./README.md).

Este arquivo evita deliberadamente repetir essas regras — ele só acrescenta:

1. O fluxo de verificação que os agentes devem executar após cada mudança.
2. O raciocínio arquitetural que não é óbvio apenas pelo `CODE_STYLE.md`.

## Idioma

`hacs.json` declara `"country": ["BR"]`, portanto o repositório fala pt-BR: documentação, docstrings, comentários, mensagens de commit, títulos e descrições de PR, changelog e toda comunicação pública. O código permanece em inglês — identificadores, nomes de arquivo e de branch, mensagens de log, e o tipo e o escopo do Conventional Commit (`fix(api): trata o 498 do portal`). Os termos nativos do domínio nunca são traduzidos. A regra completa está na seção "Idioma" do `CODE_STYLE.md`.

## Origem

Este repositório foi gerado a partir do [`ha-integration-blueprint`](https://github.com/roquerodrigo/ha-integration-blueprint). A cópia foi única e unidirecional: convenções, CI e ferramentas evoluem aqui de forma independente, e as mudanças do blueprint só chegam se alguém as portar manualmente.

## Fluxo de verificação

**Após cada mudança de código, sempre execute o lint e depois os testes, nessa ordem, antes de declarar a tarefa concluída. Execute `scripts/lint` (um wrapper fino que apenas encadeia os quatro comandos) ou execute-os diretamente:**

```bash
uv run ruff format --check .
uv run ruff check .
uv run mypy custom_components/enel_sp
uv run pytest
```

- O lint executa `ruff format`, `ruff check` e `mypy` — todos configurados em `pyproject.toml`. Corrija qualquer falha e execute de novo antes de seguir.
- O `pytest` impõe um **gate de 90 % de cobertura** (`--cov-fail-under` em `pyproject.toml`).

Os dois gates espelham o CI (`.github/workflows/ci.yml`). Só pule esta etapa quando a mudança literalmente não puder afetar lint nem testes (ex.: edições apenas no README).

## Atualização da versão do Home Assistant

A versão do Home Assistant é fixada em dois lugares, que **precisam ser atualizados juntos**; caso contrário, CI, HACS e o harness de testes se afastam:

1. `pyproject.toml`, `[dependency-groups] dev` — `homeassistant==<X.Y.Z>` (runtime/lint do CI + mypy) **e** `pytest-homeassistant-custom-component==<release correspondente>` (o harness de testes traz o próprio `homeassistant` fixado; os dois pins precisam vir da mesma release do HA, senão lint e testes resolvem cores diferentes).
2. `hacs.json` — `"homeassistant": "<X.Y.Z>"` (versão mínima do core do HA imposta pelo HACS).

Confira o pareamento no PyPI antes de commitar: o `requires_dist` do `pytest-homeassistant-custom-component` precisa listar o mesmo `homeassistant==<X.Y.Z>` fixado em `pyproject.toml`.

## Convenções que não são óbvias pelo código

A integração segue o padrão `DataUpdateCoordinator` do HA; o layout módulo a módulo está no `README.md`. Algumas escolhas não ficam evidentes pela leitura de um único arquivo:

- O estado vive em `entry.runtime_data` (descartado automaticamente no unload), **nunca** em `hass.data`.
- `data/__init__.py` guarda os aliases `type` (`EnelSpConfigEntry`, `Json*`) **e** reexporta todos os símbolos dos módulos irmãos, de modo que o código consumidor importa tudo de `.data`.
- A área do cliente não tem API pública. `api.py` é dono de todo o protocolo, obtido por engenharia reversa do bundle Angular do portal: o login SAML por `accounts.enel.com` (WSO2: `samlsso` → `login.html?sessionDataKey=…` → `commonauth` com `username`, `password`, `sessionDataKey`, `tocommonauth=true` → assertion enviada por POST a `/pt-saopaulo/saml_login` no portal, ignorando o `action` do formulário do provedor, que aponta para um `login.html` que recusa o POST com 403; não há reCAPTCHA no login web), `POST /bin/enel-br/pt-saopaulo/currentuser` com um cabeçalho `sid` para o cadastro do cliente e o `access_token`, e os serviços apoiados no SAP nos gateways MuleSoft que `/bin/enel-br/pt-saopaulo/environment` publica: `usagehistory` no `portalSPUri` e `validatecomposicaofatura` (`Funcionalidad: getIndicadores`) no `portalWEBUri`. Os serviços recebem `{Header: {Funcionalidad, CodSistema: "WEB", SistemaOrigen: "WEB", FechaHora}, Body: {I_CANAL: "ZINT", …}}` e respondem com `Body.E_RESULT` não vazio em caso de falha; eles autenticam com os cabeçalhos `enel-jwt-token`, `SID` e `CLIENT_IP: 123`, exatamente como o front-end os envia. Nada acima de `api.py` conhece HTML, SAML ou nomes de campos do SAP.
- O cliente faz login sob demanda e de novo a cada 401 ou 498, uma vez por chamada pública. Dentro de `async_login`, um 401 de `currentuser` significa que a entrega do SAML não abriu uma sessão no portal e é reportado como um erro comum da API, não como credenciais rejeitadas.
- Cada config entry recebe a própria sessão `aiohttp` de `async_create_clientsession`, para que os cookies do provedor de identidade e do portal nunca caiam na sessão compartilhada; o Home Assistant a desvincula quando a entry é descarregada, então a integração não deve fechá-la. As requisições levam um User-Agent de navegador porque o portal fica atrás do Imperva.
- O payload do coordinator é `EnelSpPayload`: a conta mais um `Mapping[número da instalação, EnelSpInstallationData]` com as instalações que o cliente ainda mantém (`AUSZDAT` em aberto). Há um dispositivo por instalação, nomeado com o apelido do portal; as entidades são descobertas dinamicamente em `sensor/__init__.py`, e `async_remove_config_entry_device` permite ao usuário excluir as que deixaram de existir.
- Os treze meses faturados vão para as estatísticas de longo prazo, não para entidades: `statistics.py` grava `enel_sp:<installation>_energy` (kWh, `unit_class` energy, leitura do medidor como estado) e `_cost` (BRL) com `async_add_external_statistics`, acrescentando apenas os meses mais novos que a última linha armazenada e reenviando os metadados a cada atualização para que os nomes acompanhem o idioma. Por isso `manifest.json` declara `recorder` em `dependencies`, e todo teste que configura uma entry precisa da fixture `recorder_mock` (`tests/conftest.py` também sobrescreve `mock_recorder_before_hass`).
- O status da fatura e a bandeira tarifária são texto livre no portal (`Paga`, `AMARELA`); `EnelSpBill.status` e `EnelSpTariffFlag.from_portal` os mapeiam para enums com fallback `unknown`, de modo que os sensores de enum nunca levantem exceção diante de uma redação nova.
- O preço da energia (`pricing.py`, `sensor/energy_price.py`) não fixa nenhum valor da instalação: a classe de consumo vem da conta mais recente cujo `VALOR_DIAS_FAT` (energia sem tributos) fecha com uma tarifa de aplicação da ANEEL, o ICMS vem de `VALOR_ICMS` (alíquota, em %) e o PIS/COFINS é deduzido da composição da conta (`TRIBUTOS` menos o ICMS, sobre o fornecimento menos o ICMS), porque a base do PIS/COFINS exclui o ICMS. O catálogo da ANEEL tem o próprio coordinator (`tariff_coordinator.py`), cuja primeira atualização não é obrigatória: uma ANEEL fora do ar não pode impedir o setup das contas. Pela mesma razão, uma falha na composição da conta nunca derruba a atualização das contas nem abre reauth.
- O reauth dispara quando o coordinator levanta `ConfigEntryAuthFailed`. Registre issues de Repairs (veja o helper de exemplo em `repairs.py`) a partir do coordinator/setup quando detectar um problema recuperável; as strings das issues ficam em `issues.<issue_id>` nos arquivos de tradução.
