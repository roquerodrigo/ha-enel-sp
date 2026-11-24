# Enel São Paulo

<!-- ha-marketplace:exclude-start -->
[![CI](https://github.com/roquerodrigo/ha-enel-sp/actions/workflows/ci.yml/badge.svg)](https://github.com/roquerodrigo/ha-enel-sp/actions/workflows/ci.yml)
[![GitHub release](https://img.shields.io/github/v/release/roquerodrigo/ha-enel-sp)](https://github.com/roquerodrigo/ha-enel-sp/releases/latest)
[![Sponsor](https://img.shields.io/badge/Sponsor-%E2%9D%A4-db61a2?logo=githubsponsors&logoColor=white)](https://github.com/sponsors/roquerodrigo)

[![Open your Home Assistant instance and open a repository in the Marketplace.](https://my.home-assistant.io/badges/marketplace_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=roquerodrigo&repository=ha-enel-sp&category=integration)
<!-- ha-marketplace:exclude-end -->

Acompanhe a sua conta de luz da Enel São Paulo no Home Assistant: o valor, o
consumo, o vencimento, se ela já foi paga e a bandeira tarifária do mês. Os
últimos meses faturados entram no painel de Energia, e um sensor calcula
quanto custa cada kWh agora, com bandeira e tributos, para você ver o custo do
que consome em tempo real. Os dados vêm da área do cliente da
[Enel São Paulo](https://www.enel.com.br/pt-saopaulo.html), com o mesmo login
que você usa no site.

## Recursos

- Veja o valor, o consumo e o vencimento da conta mais recente, e se ela está
  paga, em aberto ou vencida.
- Saiba quanto você deve no total e quantas contas aguardam pagamento, e crie
  automações que lembram você antes do vencimento.
- Acompanhe a bandeira tarifária em vigor.
- Tenha no painel de Energia o consumo e o valor de cada mês faturado,
  inclusive dos meses anteriores à instalação da integração.
- Use o sensor Preço da energia com um medidor seu (no quadro ou numa tomada
  inteligente) para ver no painel de Energia quanto custa o que você consome
  agora.
- Cada unidade consumidora da sua conta vira um dispositivo próprio, com o
  apelido que você deu a ela no site da Enel.

## Requisitos

- Home Assistant 2026.7.2 ou mais recente.
- Um cadastro na área do cliente da Enel São Paulo: e-mail, CPF ou celular, e
  a senha.
- Acesso do Home Assistant à internet.

<!-- ha-marketplace:exclude-start -->
## Instalação

### Marketplace do Home Assistant (recomendado)

1. Selecione o botão **Open your Home Assistant instance** acima, ou vá em
   **Configurações → Marketplace**, selecione **Adicionar a partir de link**,
   informe `https://github.com/roquerodrigo/ha-enel-sp` em
   **Link do GitHub** e selecione **Adicionar**.
2. Selecione **Instalar**.
3. Reinicie o Home Assistant.

O Marketplace vem com o Home Assistant 2026.11 e versões posteriores. Nas
versões anteriores, adicione este repositório ao HACS como repositório
personalizado do tipo **Integração** e instale a partir de lá.

### Manual

1. Baixe o `enel_sp.zip` da
   [última release](https://github.com/roquerodrigo/ha-enel-sp/releases/latest).
2. Extraia o conteúdo em `config/custom_components/enel_sp/`.
3. Reinicie o Home Assistant.
<!-- ha-marketplace:exclude-end -->

## Configuração

Vá em **Configurações → Dispositivos e serviços → Adicionar integração**,
procure **Enel São Paulo** e preencha o formulário.

| Campo                  | O que informar                                      |
|------------------------|-----------------------------------------------------|
| E-mail, CPF ou celular | O login que você usa na área do cliente da Enel     |
| Senha                  | A senha da área do cliente                          |

A primeira configuração pode levar alguns segundos, porque o site da Enel
demora para responder. Cada login só pode ser adicionado uma vez.

Para trocar o login ou a senha depois, abra a integração e selecione
**Reconfigurar**. O login precisa ser o mesmo usado na configuração (o mesmo
e-mail, CPF ou celular). Se você mudar a senha no site da Enel, o Home
Assistant pede a nova.

## Opções

Abra a integração e selecione **Configurar**.

| Opção                            | Padrão          | Valores     | Efeito                                                |
|----------------------------------|-----------------|-------------|-------------------------------------------------------|
| Intervalo de consulta (segundos) | 3600 (uma hora) | 300 ou mais | De quanto em quanto tempo o site da Enel é consultado |

As contas saem uma vez por mês, então uma hora basta para ver uma conta nova
ou um pagamento no mesmo dia.

## Entidades

Cada unidade consumidora ativa da conta vira um dispositivo, com o apelido
dado a ela no site da Enel (ou o número da instalação, se ela não tiver
apelido). O apelido também aparece como modelo do dispositivo, então continua
visível se você o renomear no Home Assistant. Todas as entidades são sensores.

| Entidade            | Unidade ou estados                                   | O que mostra                                                  |
|---------------------|------------------------------------------------------|---------------------------------------------------------------|
| Valor da conta      | BRL                                                  | O valor da conta mais recente                                 |
| Consumo da conta    | kWh                                                  | A energia faturada na conta mais recente                      |
| Vencimento da conta | Data e hora                                          | O vencimento da conta mais recente                            |
| Situação da conta   | Paga, Em aberto, Vencida ou Desconhecida             | Se a conta mais recente já foi paga                           |
| Leitura do medidor  | kWh                                                  | O número lido no medidor para a conta mais recente            |
| Valor em aberto     | BRL                                                  | A soma das contas que ainda não constam como pagas            |
| Contas em aberto    | Número de contas                                     | Quantas contas ainda não constam como pagas                   |
| Bandeira tarifária  | Verde, Amarela, Vermelha patamar 1, Vermelha patamar 2 ou Desconhecida | A bandeira em vigor informada pela Enel     |
| Preço da energia    | BRL/kWh                                              | Quanto custa cada kWh consumido agora, com bandeira e tributos |

Os atributos trazem mais detalhes, úteis em templates e automações:

- Todos os sensores: `installation_number`, `meter_serial` e o mês da conta
  (`bill_year`, `bill_month`).
- Valor da conta: `icms`, `taxes` (tributos), `interest` (juros) e `days`
  (dias faturados).
- Consumo da conta: `days` e `daily_average` (média diária em kWh).
- Situação da conta: `portal_status`, o texto exatamente como o site da Enel
  mostra.
- Preço da energia: cada parcela do preço, descrita em Como funciona, abaixo.

Uma unidade consumidora nova na sua conta aparece sozinha, sem reiniciar. Uma
que deixa de aparecer no site da Enel fica indisponível, e você pode excluir o
dispositivo dela.

### Histórico das contas

Os sensores mostram só a conta mais recente. Os meses anteriores que a Enel
mantém (em geral, treze) entram nas estatísticas de longo prazo do Home
Assistant, em duas séries por unidade consumidora, com o nome no idioma do
Home Assistant:

| Série                          | Unidade | O que guarda                     |
|--------------------------------|---------|----------------------------------|
| `<apelido> Consumo da conta`   | kWh     | A energia faturada em cada mês   |
| `<apelido> Valor da conta`     | BRL     | O valor de cada conta            |

Cada mês fica registrado no primeiro dia do mês da conta, e os meses novos
entram conforme as contas saem. Você pode usar as duas séries no painel de
Energia ou num card **Gráfico de estatísticas**.

As séries continuam no Home Assistant se você remover a integração. Para
apagá-las, vá em **Configurações → Ferramentas → Estatísticas**.

### Painel de Energia

Vá em **Configurações → Energia** e, em **Rede elétrica**, selecione
**Adicionar conexão à rede**. Há dois jeitos de usar a integração ali.

Sem medidor próprio, com o consumo das contas:

1. Em **Energia importada da rede**, escolha a série `<apelido> Consumo da
   conta`.
2. Em **Rastreamento de custos**, escolha **Usar uma entidade que rastreie os
   custos totais** e, em **Entidade com os custos totais**, a série
   `<apelido> Valor da conta`.

O painel passa a mostrar o consumo e o valor de cada mês, inclusive dos meses
anteriores à instalação da integração. Como a Enel informa um número por mês,
o painel não mostra o consumo por dia ou por hora.

Com um medidor próprio, que mede o consumo ao vivo:

1. Em **Energia importada da rede**, escolha o sensor de energia do seu
   medidor.
2. Em **Rastreamento de custos**, escolha **Usar uma entidade com preço
   atual** e, em **Entidade com o preço atual**, o sensor Preço da energia.

O painel passa a mostrar quanto custou cada hora de consumo. Use um jeito ou o
outro, não os dois para a mesma casa, para o consumo não aparecer em dobro.

## Como funciona

A integração entra na área do cliente da Enel São Paulo com o seu login e lê
as unidades consumidoras da conta, as contas de cada uma e a composição do
valor delas. Isso acontece no intervalo de consulta, pela internet. As
unidades que você não mantém mais na Enel são ignoradas.

Os últimos dados ficam salvos no Home Assistant. Depois de um reinício, os
sensores mostram os valores na hora, e o site da Enel é consultado em segundo
plano. Se o site ficar fora do ar, os sensores mantêm os últimos valores por
até 24 horas antes de ficarem indisponíveis.

### Preço da energia

O sensor Preço da energia refaz o cálculo da conta da Enel para um kWh:

```
preço = (TUSD + TE + adicional da bandeira) / ((1 − ICMS) × (1 − PIS/COFINS))
```

Nada é fixo na integração. Cada parcela vem de uma fonte que acompanha a sua
unidade consumidora:

| Parcela               | De onde vem                                                                                                                   |
|-----------------------|-------------------------------------------------------------------------------------------------------------------------------|
| TUSD e TE             | A tarifa homologada pela ANEEL em vigor hoje, nos [dados abertos da ANEEL](https://dadosabertos.aneel.gov.br/dataset/tarifas-distribuidoras-energia-eletrica). A classe de consumo (residencial, rural, comercial) é descoberta pelas suas contas. |
| Adicional da bandeira | A bandeira que a ANEEL acionou no mês, nos [dados abertos da ANEEL](https://dadosabertos.aneel.gov.br/dataset/bandeiras-tarifarias). |
| ICMS                  | A alíquota informada na conta mais recente.                                                                                   |
| PIS/COFINS            | Calculado a partir da composição da conta mais recente, porque muda todo mês.                                                 |

As tarifas e as bandeiras são consultadas na ANEEL a cada seis horas. Se a
ANEEL ficar fora do ar, valem as últimas conhecidas.

Quando nenhuma conta bate com uma tarifa homologada, como na tarifa social,
que é cobrada por faixas de consumo, o sensor usa a tarifa média da conta mais
recente (o valor da energia sem tributos dividido pelo consumo). O atributo
`tariff_source` mostra qual foi usada: `aneel` ou `bill`.

Os atributos do sensor mostram cada parcela: `tariff`, `tusd`, `te`,
`bandeira_tarifaria`, `bandeira_tarifaria_surcharge`, `icms_rate` e
`pis_cofins_rate` (em %), `price_before_taxes`, a classe de consumo
(`tariff_subgroup`, `tariff_class`, `tariff_subclass`), a vigência e a
resolução da tarifa (`tariff_valid_from`, `tariff_resolution`), o mês da conta
de onde vieram os tributos (`tax_bill_year`, `tax_bill_month`) e `other_items`,
explicado em Limitações conhecidas, abaixo.

## Solução de problemas

**O Home Assistant pede a senha de novo.** O site da Enel recusou o login
salvo, em geral porque a senha mudou. Informe a senha atual no aviso que
aparece em **Configurações → Dispositivos e serviços**.

**A integração não termina de configurar.** O site da Enel pode estar fora do
ar ou lento. O Home Assistant tenta de novo sozinho. Confira se você consegue
entrar na área do cliente pelo navegador.

**O Preço da energia fica sem valor.** O cálculo precisa de pelo menos uma
conta com a composição do valor discriminada. Espere a próxima atualização, ou
a próxima conta, se a unidade consumidora for nova.

**A conta nova ainda não apareceu.** A integração mostra o que a área do
cliente mostra. Se a conta já está no site, espere o intervalo de consulta ou
reduza-o em **Configurar**.

**Outro problema.** Na página da integração, selecione **Fazer download dos
diagnósticos** e anexe o arquivo a uma
[issue](https://github.com/roquerodrigo/ha-enel-sp/issues). O login, a senha,
o nome, o endereço e os números da unidade consumidora são removidos do
arquivo.

## Limitações conhecidas

- A integração atende só a Enel Distribuição São Paulo. Contas de outras
  distribuidoras da Enel não funcionam.
- Os dados são mensais: o consumo vem das contas, não do medidor em tempo
  real.
- Uma conta que a Enel corrige depois de publicada não é atualizada no
  histórico.
- O Preço da energia considera a tarifa convencional de baixa tensão. Em
  outras modalidades, como a tarifa branca, ele usa a tarifa média da última
  conta, que não varia com o horário.
- O Preço da energia cobre só o que a Enel cobra por kWh. Ficam de fora:
  - os itens fixos da conta, como a contribuição de iluminação pública
    (COSIP), e créditos ou ajustes avulsos. O total deles na última conta fica
    no atributo `other_items`;
  - a mudança de faixa do ICMS no mês: a alíquota depende do consumo total do
    mês (em São Paulo, o consumo residencial baixo é isento), e o sensor usa a
    da conta mais recente;
  - a variação mensal do PIS/COFINS, que só se conhece quando a conta sai. A
    da conta anterior costuma diferir em poucos décimos de ponto percentual.

## Apoie o projeto

Esta integração é desenvolvida e mantida no meu tempo livre. Se ela for útil
para você, considere
[patrocinar o trabalho](https://github.com/sponsors/roquerodrigo). É o que
garante as correções, os testes e as novas versões.

Bugs e sugestões: abra uma [issue](https://github.com/roquerodrigo/ha-enel-sp/issues).

<!-- ha-marketplace:exclude-start -->
## Contribuindo

Veja o [CONTRIBUTING.md](CONTRIBUTING.md) para o ambiente de desenvolvimento e
o fluxo de trabalho, e o [CODE_STYLE.md](CODE_STYLE.md) para as convenções de
código.

## Licença

[MIT](LICENSE)
<!-- ha-marketplace:exclude-end -->
