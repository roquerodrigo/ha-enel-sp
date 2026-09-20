# Assets de marca

O Home Assistant 2026.3 e posteriores servem as imagens deste diretório
diretamente (`/api/brands/integration/enel_sp/<image>`), com prioridade sobre o
CDN do [home-assistant/brands](https://github.com/home-assistant/brands), de
modo que a integração exibe o próprio ícone e logo sem uma submissão ao brands.

| Arquivo       | Conteúdo                                         | Tamanho |
| ------------- | ------------------------------------------------ | ------- |
| `icon.png`    | logotipo "enel BRASIL" centralizado num quadrado | 256×256 |
| `icon@2x.png` | idem                                             | 512×512 |
| `logo.png`    | logotipo "enel BRASIL", paisagem                 | 239×128 |
| `logo@2x.png` | idem                                             | 478×256 |

A origem é o logotipo vetorial que a própria área do cliente exibe,
`https://www.enel.com.br/content/dam/enel-br/pt-saopaulo/private-area/icons/enel-logo.svg`
(viewBox de 100×79, verde Enel `#08A859`, azul `#253468` e amarelo `#FECB2C`).
Ele foi rasterizado com o Chrome headless sobre fundo transparente
(`--default-background-color=00000000`, depois de elevar o tamanho declarado do
SVG para 2000×1580 px), recortado até o conteúdo e redimensionado com filtro
Lanczos; o ícone mantém o logotipo em 90 % do quadrado, centralizado na
vertical.

As regras do repositório brands continuam valendo: ícones são quadrados de
256/512 px, logos mantêm a proporção da marca com o lado menor entre 128 e
256 px (256 e 512 px para os arquivos `@2x`), fundo transparente.
