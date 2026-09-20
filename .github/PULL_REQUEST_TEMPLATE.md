## Resumo

<!-- 1 a 3 itens descrevendo o que mudou e por quê. -->

## Tipo de mudança

- [ ] Correção de bug
- [ ] Nova funcionalidade
- [ ] Refatoração / limpeza
- [ ] Documentação
- [ ] Ferramentas / CI

## Plano de teste

- [ ] `uv run ruff format --check .`, `uv run ruff check .` e `uv run mypy custom_components/enel_sp` passam
- [ ] `pytest` passa com o gate de 90 % de cobertura
- [ ] Todos os locales de tradução atualizados (se strings exibidas ao usuário mudaram)

## Checklist

- [ ] O código está em inglês; documentação, docstrings e comentários, em pt-BR; termos nativos do domínio sem tradução
- [ ] Uma classe de nível superior por arquivo
- [ ] CLAUDE.md / README atualizados se a arquitetura ou o fluxo de trabalho mudou
- [ ] Versão do `manifest.json` incrementada, se for uma release
