# Plan — Reconstrução `premortem-code` (execução)

Ref spec: `../specs/premortem-code-reconstruction.md`. Executar **uma task por vez**,
commit atômico por task, validar antes de avançar. Sem spawn (sem paralelismo real aqui).

## Ordem de execução

| # | Task | Entregável | Validação | Commit |
|---|---|---|---|---|
| 0 | Confirmar licenças das fontes | nota no README | curl LICENSE dos 3 repos-chave | (parte de T8) |
| T1 | Catálogo de fragilidade | `assets/fragility-catalog-core.md` | revisão visual; 10 categorias | `feat: fragility catalog` |
| T2 | Protocolo de verificação | `assets/verification-protocol.md` | hard gates presentes | `feat: verification protocol` |
| T3 | Prompt do subagente | `assets/subagent-prompt.md` | framing adversarial | `feat: subagent prompt` |
| T4 | Template de saída | `assets/premortem-md-template.md` | bate com contrato README; força file:line | `feat: output template` |
| T5 | 6 addenda de stack | `assets/stack-{python-fastapi,postgres,redis-arq,qdrant,agents-mcp,docker-k8s}.md` | cada um com 5 seções | `feat: stack addenda (6 confirmed)` |
| T6 | Exporter SARIF | `scripts/sarif_export.py` | SARIF válido + warn em location ruim | `feat: sarif exporter` |
| T7 | SKILL.md | `SKILL.md` | ≤500 linhas, frontmatter válido, desc ≤1024 | `feat: SKILL.md core` |
| T8 | Docs + licença | `README.md`, `LICENSE`, créditos | links corretos | `docs: readme + provenance` |
| T9 | Validação E2E | — | instalar + rodar num diff real | `test: e2e validation` |

## Gate de qualidade por task
- Após T4 e T7: `python -c "import yaml; yaml.safe_load(...)"` no frontmatter.
- Após T6: rodar exporter num PREMORTEM de exemplo + validar schema + caso location não-estruturada.
- Após T9: checklist de aceitação do spec (todos os itens).

## Pós-execução
- Commit final + push (repo solo pessoal → main direto, ok por CLAUDE.md).
- Atualizar MEMORY.md (projeto novo + decisões).
- Oferecer: (a) instalar de fato, (b) rodar otimização de description (skill-creator), (c) gerar os 8 stacks restantes.
