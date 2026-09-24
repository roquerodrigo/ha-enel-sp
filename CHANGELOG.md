# Changelog

## [1.1.0](https://github.com/roquerodrigo/ha-enel-sp/compare/v1.0.0...v1.1.0) (2026-09-24)


### Funcionalidades

* **sensor:** adiciona o preço da energia com tarifa, bandeira e tributos ([0ce624d](https://github.com/roquerodrigo/ha-enel-sp/commit/0ce624d5c89ad5c3b45ef3023723cf933fd1ae91))


### Dependências de desenvolvimento

* **deps-dev:** bump ruff in the python-deps group ([77f0365](https://github.com/roquerodrigo/ha-enel-sp/commit/77f03652748c583c7d6b301f65d3953e7f350fb1))


### Integração contínua

* adiciona a análise do CodeQL ([784f81e](https://github.com/roquerodrigo/ha-enel-sp/commit/784f81e14f4d16144e8ee4fb82824d70c509eeb3))

## 1.0.0 (2026-09-20)


### Funcionalidades

* integração da Enel São Paulo para o Home Assistant: um dispositivo por instalação ativa, com sensores da conta mais recente, das contas em aberto, da leitura do medidor e da bandeira tarifária
* estatísticas de longo prazo de energia e custo a partir dos meses faturados
* login SAML pela conta Enel, com reautenticação e reconfiguração pela interface
