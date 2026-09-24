# Enel São Paulo para Home Assistant

[![CI](https://github.com/roquerodrigo/ha-enel-sp/actions/workflows/ci.yml/badge.svg)](https://github.com/roquerodrigo/ha-enel-sp/actions/workflows/ci.yml)
[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

[![Open your Home Assistant instance and open the repository inside HACS.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roquerodrigo&repository=ha-enel-sp&category=integration)

---

Integração custom para o [Home Assistant](https://www.home-assistant.io/) que
acessa a área do cliente da [Enel Distribuição São Paulo](https://www.enel.com.br/pt-saopaulo.html),
a distribuidora de energia elétrica da região metropolitana de São Paulo. Ela
faz login com as mesmas credenciais usadas no site e transforma cada instalação
que a conta ainda mantém em um dispositivo com as suas contas e o seu consumo.

## Entidades

É criado um dispositivo por instalação ativa, nomeado com o apelido dado a ela
no portal ("Casa"), cada um com nove sensores. O apelido também aparece
como modelo no cartão do dispositivo, então continua visível se você renomear o
dispositivo no Home Assistant:

| Sensor | Unidade | Classe | O que informa |
|---|---|---|---|
| Valor da conta | BRL | monetary, `total` | Valor da conta mais recente; `last_reset` é o primeiro dia do mês de faturamento. Os atributos trazem ICMS, tributos, juros e o número de dias. |
| Consumo da conta | kWh | energy, `total` | Energia faturada no mês mais recente, com a média diária como atributo. |
| Vencimento da conta | timestamp | timestamp | Data de vencimento da conta mais recente, à meia-noite local, para que o front-end mostre quanto tempo falta. |
| Situação da conta | enum | `paid`, `open`, `overdue`, `unknown` | Situação de pagamento da conta mais recente; o texto original do portal fica no atributo `portal_status`. |
| Leitura do medidor | kWh | energy, `total_increasing` | Valor do contador lido para a conta mais recente. Use-o como fonte de eletricidade no painel de Energia. |
| Valor em aberto | BRL | monetary | Total das contas aguardando pagamento, incluindo as vencidas. |
| Contas em aberto | contagem | measurement | Número de contas aguardando pagamento. |
| Bandeira tarifária | enum | `green`, `yellow`, `red_level_1`, `red_level_2` | Bandeira tarifária em vigor para a conta. |
| Preço da energia | BRL/kWh | `measurement` | Quanto custa cada kWh consumido agora, com bandeira, ICMS, PIS e COFINS. Veja [Preço da energia](#preço-da-energia). |

Todo sensor expõe `installation_number`, `meter_serial`, `bill_year` e
`bill_month` como atributos. As contas são publicadas mensalmente, por isso o
intervalo padrão de consulta é de uma hora (configurável nas opções da
integração).

## Histórico e o painel de Energia

O estado de um sensor carrega apenas a conta mais recente, então os treze meses
faturados que o portal mantém são importados para as estatísticas de longo
prazo do Home Assistant. Cada instalação recebe duas estatísticas externas,
nomeadas com a instalação e o sensor correspondente ("Casa Consumo da
conta"):

| Id da estatística | Unidade | O que guarda |
|---|---|---|
| `enel_sp:<installation>_energy` | kWh | Energia de cada mês faturado, com a leitura do medidor como estado |
| `enel_sp:<installation>_cost` | BRL | Valor de cada mês faturado |

O valor de cada mês é registrado no primeiro dia do mês de faturamento. As
atualizações seguintes só acrescentam meses mais novos que o último armazenado.
Escolha a estatística de energia como fonte de eletricidade em *Configurações →
Painéis → Energia*, ou plote qualquer uma das séries com um card de gráfico de
estatísticas. Remover a integração mantém as estatísticas; exclua-as em
*Ferramentas de desenvolvedor → Estatísticas* se não as quiser mais.

## Preço da energia

O sensor **Preço da energia** serve para multiplicar pela energia medida ao vivo
(um medidor no quadro, uma tomada inteligente). Ele reproduz a conta da Enel
item a item:

```
preço = (TUSD + TE + adicional da bandeira) / ((1 − ICMS) × (1 − PIS − COFINS))
```

O ICMS incide sobre o valor com todos os tributos, e o PIS e a COFINS sobre
esse valor sem o ICMS, por isso os dois fatores se multiplicam. Nada é fixo na
integração; cada parcela vem de uma fonte que acompanha a sua instalação:

| Parcela | Origem |
|---|---|
| TUSD e TE | Tarifa de aplicação homologada pela ANEEL ([dados abertos](https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica)) em vigor hoje. A classe de consumo (residencial, rural, comercial…) é descoberta pelas suas contas: a conta mais recente cujo valor da energia sem tributos fecha com uma tarifa homologada revela a classe. |
| Adicional da bandeira | Bandeira que a ANEEL acionou no mês corrente ([dados abertos](https://dadosabertos.aneel.gov.br/dataset/bandeiras-tarifarias)). |
| ICMS | Alíquota informada na conta mais recente. |
| PIS e COFINS | Deduzidos da conta mais recente, pela composição do valor que o portal discrimina (esses tributos mudam todo mês). |

Quando nenhuma conta fecha com uma tarifa homologada, como na tarifa social,
que é cobrada por faixas de consumo, o sensor usa a tarifa efetiva da conta
mais recente (valor da energia sem tributos dividido pelo consumo), e o
atributo `tariff_source` passa de `aneel` para `bill`. Os atributos trazem cada
parcela: `tusd`, `te`, `tariff`, `bandeira_tarifaria`,
`bandeira_tarifaria_surcharge`, `icms_rate`, `pis_cofins_rate`,
`price_before_taxes`, a classe e a resolução da ANEEL, e a conta de onde vieram
as alíquotas.

Para ver o custo no painel de Energia, escolha o sensor do seu medidor como
fonte de eletricidade e, em *Usar uma entidade com o preço atual*, este sensor.

O preço cobre só o que a Enel cobra por kWh. Ficam de fora:

- **Itens fixos da conta**, como a contribuição de iluminação pública (COSIP),
  que é um valor por faixa de consumo do mês, e créditos ou ajustes avulsos. O
  total deles na última conta fica no atributo `other_items`.
- **Mudanças de faixa de ICMS no mês**: a alíquota depende do consumo total do
  mês (em São Paulo, consumo residencial baixo é isento). O sensor usa a
  alíquota da conta mais recente.
- **A variação mensal do PIS e da COFINS**, que só se conhece quando a conta
  sai. A alíquota da conta anterior costuma diferir em poucos décimos de ponto
  percentual.

## Instalação

### HACS

1. Adicione `https://github.com/roquerodrigo/ha-enel-sp` como repositório
   personalizado do tipo *Integração*, ou clique no badge acima.
2. Instale **Enel São Paulo** e reinicie o Home Assistant.
3. Vá em *Configurações → Dispositivos e serviços → Adicionar integração*,
   escolha **Enel São Paulo** e informe o e-mail, CPF ou celular e a senha
   usados na área do cliente.

### Manual

Copie `custom_components/enel_sp/` para o diretório `custom_components/` da
configuração do seu Home Assistant e reinicie.

## Como funciona

A área do cliente é uma aplicação Angular que conversa com serviços apoiados no
SAP por meio de gateways MuleSoft; não há API pública. A integração aciona os
mesmos endpoints que o site usa:

1. Login pelo provedor de identidade SAML da Enel: `GET accounts.enel.com/samlsso`
   inicia uma sessão de login, as credenciais são enviadas por POST a
   `commonauth` com o respectivo `sessionDataKey`, e a assertion SAML que o
   provedor devolve é entregue ao `saml_login` do portal. Credenciais
   rejeitadas voltam como um redirecionamento para a página de login.
2. `POST /bin/enel-br/pt-saopaulo/currentuser` retorna o cadastro do cliente:
   nome, bandeira tarifária, as instalações (`ET_INST`, com as chaves SAP de
   cada uma) e o `access_token` que os serviços esperam no cabeçalho
   `enel-jwt-token`.
3. `POST <gateway>/usagehistory`, para cada instalação ativa, retorna os treze
   meses faturados (`ET_HISTORICO`): valor, energia, dias, vencimento,
   situação, tributos, a alíquota de ICMS e a leitura do medidor. O endereço
   dos gateways vem de `/bin/enel-br/pt-saopaulo/environment`.
4. `POST <gateway web>/validatecomposicaofatura` (`getIndicadores`) retorna a
   composição do valor de cada conta (`ET_COMPOSICAO`): energia, distribuição,
   transmissão, encargos, perdas, tributos e demais itens. Uma falha aqui não
   afeta as contas; o preço da energia continua com a última composição
   conhecida.

As tarifas e as bandeiras vêm da API CKAN do portal de dados abertos da ANEEL
(`datastore_search`), consultada a cada seis horas; se ela estiver fora do ar,
o último catálogo continua valendo.

Qualquer 401 do portal ou dos serviços significa que uma das sessões expirou; o
cliente faz login de novo uma vez e repete a chamada. Indisponibilidades curtas
são absorvidas por 24 horas antes de as entidades ficarem indisponíveis, e
credenciais rejeitadas iniciam o fluxo de reautenticação. Instalações que o
cliente não mantém mais (`AUSZDAT` no passado) são ignoradas.

## Desenvolvimento

```bash
scripts/setup                              # cria o .venv e instala as dependências (uv sync)
scripts/develop                            # inicia o Home Assistant em modo debug com a integração carregada
scripts/lint                               # ruff format --check, ruff check, mypy e pytest
uv run ruff format --check .               # verifica a formatação
uv run ruff check .                        # lint
uv run mypy custom_components/enel_sp      # verificação de tipos
uv run pytest                              # executa os testes com o gate de 90 % de cobertura
```

Os dois scripts rodam por meio do `uv`, que gerencia o `./.venv`
automaticamente. O HA roda com a configuração em `config/` e o `PYTHONPATH`
apontando para `custom_components/` — sem symlinks. Para recriar os IDs de
entidades/dispositivos durante o desenvolvimento:

```bash
rm config/.storage/core.entity_registry config/.storage/core.device_registry
```

### Testes no Docker

O `compose.yaml` executa, na porta 8124, a release do Home Assistant à qual os
testes estão fixados, com `config/` como diretório de configuração e
`custom_components/enel_sp/` montado como somente leitura dentro dele, de modo
que o container sempre roda a árvore de trabalho:

```bash
docker compose up -d          # inicia o Home Assistant em http://localhost:8124
docker compose logs -f        # acompanha o log (a integração registra em nível debug)
docker compose restart        # recarrega a integração após uma mudança de código
docker compose down           # para; config/ mantém o onboarding, os usuários e as entries
```

Na primeira inicialização, conclua o onboarding e depois adicione
**Enel São Paulo** em *Configurações → Dispositivos e serviços*. O `config/` é
compartilhado com `scripts/develop`, portanto não execute os dois ao mesmo
tempo.

As convenções para quem contribui ficam em [`CODE_STYLE.md`](./CODE_STYLE.md);
as notas de arquitetura para agentes de IA, em [`CLAUDE.md`](./CLAUDE.md).
Instale os hooks de pre-commit uma vez por clone com `pre-commit install`.

## Layout

```
custom_components/enel_sp/
├── __init__.py        # async_setup_entry / unload / reload / remoção de dispositivo
├── aneel_api.py       # cliente dos dados abertos da ANEEL: tarifas e bandeiras
├── api.py             # cliente do portal: login SAML, usuário atual, histórico e composição das contas
├── brand/             # assets de marca
├── config_flow.py     # passos user / reauth / reconfigure
├── const.py           # DOMAIN, LOGGER, URLs do portal, ATTRIBUTION, padrões de scan interval
├── coordinator.py     # DataUpdateCoordinator com período de tolerância a indisponibilidades
├── data/              # um TypedDict/dataclass por arquivo; aliases type em __init__.py
│   ├── account.py     # cadastro do cliente: bandeira tarifária e instalações
│   ├── bill.py        # um mês faturado, com a classificação da situação
│   ├── installation.py
│   ├── installation_data.py
│   ├── payload.py     # payload do coordinator
│   └── …              # formatos brutos dos serviços, config, options, diagnostics, runtime
├── diagnostics.py     # diagnóstico para download, com as credenciais ocultadas
├── entity.py          # CoordinatorEntity base vinculada a uma instalação
├── exceptions/        # um arquivo por classe de exceção
├── icons.json         # ícones das entidades indexados por translation_key
├── manifest.json
├── options_flow.py    # OptionsFlow com scan_interval
├── pricing.py         # cálculo do preço da energia a partir das contas e da ANEEL
├── repairs.py         # plataforma de Repairs
├── sensor/            # um arquivo por classe de sensor
├── statistics.py      # importação das estatísticas de longo prazo
├── tariff_coordinator.py  # DataUpdateCoordinator do catálogo da ANEEL
└── translations/
    ├── en.json
    └── pt-BR.json
```

## CI

Todos os workflows chamam os workflows reutilizáveis de [`roquerodrigo/workflows`](https://github.com/roquerodrigo/workflows):

- **`ci.yml`** — ruff (check + format) + mypy, pytest com o gate de cobertura e a validação `hassfest` (o validador do HACS fica desligado enquanto o repositório é privado); push/PR para a `main`
- **`release.yml`** — release-please, condicionado a uma execução verde do CI na `main`; quando uma release é criada, anexa a ela o `enel_sp.zip` que o HACS baixa (`zip_release` em `hacs.json`)
- **`auto-assign.yml`** — atribui novas issues/PRs ao code owner

## Licença

[MIT](LICENSE)
