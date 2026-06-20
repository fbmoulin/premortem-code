# Spec — Incremento: 8 stack addenda restantes + description

Data: 2026-06-19 · Repo: `~/projetos-2026/premortem-code` · Tipo: incremento aditivo.

## Objetivo
Completar a cobertura de stacks da skill `premortem-code` adicionando os 8 addenda que
ficaram fora do primeiro ciclo, mais ajustar a `description` e a tabela de detecção.

## Escopo
**Dentro:** 8 novos `assets/stack-*.md` para `supabase`, `frontend`, `vercel`, `n8n`,
`playwright`, `aws-cdk`, `anthropic-skills`, `finetuning`; atualizar a tabela de detecção
no `SKILL.md` (6→14 linhas); ajustar a `description` sem estourar 1024 ch; atualizar
README (6→14 stacks).
**Fora:** loop de otimização de description via `skill-creator run_loop` (precisa de
`claude -p`; ofereço depois); novos testes (os addenda são markdown).

## Arquitetura / contrato dos addenda
Cada `stack-*.md` segue EXATAMENTE o formato dos 6 existentes (5 seções `##`):
`When this loads` → `Extends` (Category N do core) → `Failure-mode patterns` →
`Verification questions` → `Common false positives`. Texto próprio; conceitos podem ser
gerais (não copiar fontes). Termina com a nota de proveniência quando aplicável.

## Decisão: a `description` NÃO pode listar 14 stacks
Em 881 ch com 6 nomes; 14 nomes provavelmente passa de 1024. **Regra:** se a lista
completa couber ≤1024, listar as 14; senão, **generalizar** ("common backend, frontend,
infra, and AI/LLM stacks") e manter a tabela completa no corpo. Verificar com contagem.
A regra de fallback ("stack sem addendum → core catalogue") permanece — agora raramente
acionada.

## Task decomposition
- **S1** — Fan-out: 4 agentes paralelos, cada um escreve 2 addenda (file-disjoint), tendo
  os 6 existentes + o core como modelo. (Usa a skill dispatching-parallel-agents.)
- **S2** — Integração: gravar os 8 arquivos, atualizar tabela de detecção (14 linhas),
  ajustar description (regra acima), atualizar README.
- **S3** — Validação: 14 assets stack + 4 base = 18; cada novo com 5 seções `##`;
  description ≤1024 sem `<>`; SKILL.md ≤500 linhas; frontmatter YAML válido; testes 8/8.

## Riscos
- **Variância de qualidade entre agentes** → mitigação: prompt com o template exato + 1
  addendum existente como exemplar; integração revisa cada um.
- **Description estourar 1024** → mitigação: regra de generalização + contagem.
- **SKILL.md passar 500 linhas** → improvável (só +8 linhas na tabela); verificar.

## Critérios de aceitação — VERIFICADOS 2026-06-19
- [x] 8 novos `stack-*.md`, cada um com as 5 seções (fan-out 4 agentes paralelos).
- [x] `assets/` = 18 arquivos (4 base + 14 stack).
- [x] Tabela de detecção = 14 linhas; description 966 ch sem `<>`; SKILL.md 121 linhas.
- [x] README atualizado (14 stacks). Testes 8/8. (commit + push abaixo.)
- Decisão da description: as 14 couberam em 966≤1024 → listadas (sem generalizar).
