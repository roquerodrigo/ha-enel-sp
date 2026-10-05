# Changelog

## [1.1.1](https://github.com/roquerodrigo/ha-enel-sp/compare/v1.1.0...v1.1.1) (2026-10-05)


### Dependências

* **deps:** bump urllib3 from 2.7.0 to 2.8.0 ([f610fbb](https://github.com/roquerodrigo/ha-enel-sp/commit/f610fbbb754d750d0170c1368bde3dbadb2c56b6))
* **deps:** bump virtualenv from 21.7.9 to 21.7.13 ([2452cb6](https://github.com/roquerodrigo/ha-enel-sp/commit/2452cb6f6fb3c265bd3953721aa9faf94c24df6b))


### Dependências de desenvolvimento

* **deps-dev:** bump ruff in the python-deps group ([b9a2350](https://github.com/roquerodrigo/ha-enel-sp/commit/b9a235085d9653b1bd8c14a3fb9cf89277c847c8))
* **deps-dev:** bump the python-deps group with 2 updates ([334869a](https://github.com/roquerodrigo/ha-enel-sp/commit/334869afcbc682aae7649c1946d124f865426f89))


### Sistema de build

* **release:** atualiza o uv.lock pelo release-please ([b0f6c4e](https://github.com/roquerodrigo/ha-enel-sp/commit/b0f6c4e374aabae670542d741af1d4ff18d33f48))

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
