# Spec — Plan/spec pre-mortem mode

Status: **EM EXECUÇÃO** (aprovado pelo Felipe). Branch: `claude/plan-premortem-mode-ppe60t`.
Data: 2026-06-27 · Método: SDD + pesquisa do ecossistema de skills do usuário (superpowers).

## Objetivo

Adicionar ao `premortem-code` um **modo de pre-mortem adversarial para documentos de plano/spec**
(não só código). Hoje a skill é ancorada em diff/`file:line`/stack; este modo aceita um **plano/spec
em markdown** como alvo, assume que **a execução do plano já falhou**, e enumera por quê — emitindo o
mesmo veredito `GO/REFINE/REWORK/ABANDON`.

## Por quê (gap identificado na pesquisa)

As skills que o usuário já tem cobrem o resto; só falta isto:
- Auditoria de execução → `verification-before-completion` (já tem).
- Cobertura de plano (construtiva) → `writing-plans` self-review + `plan-review-cycle` (já tem).
- Risco do código → `premortem-code` modo código (já tem).
- **Pre-mortem ADVERSARIAL de um plano** → ninguém faz. `writing-plans` só faz auto-revisão de cobertura;
  `plan-review-cycle` é construtivo. Este modo preenche exatamente esse buraco.

## Escopo

- **In:** novo `assets/plan-failure-catalog.md` (10 categorias de falha de plano); seção
  `## Pre-mortem of a plan or spec` no `SKILL.md`; nota de âncora `file:section` no template e no
  protocolo de verificação; bump de versão 2.1.0; README; 1 par de fixtures (plano falho/limpo).
- **Out:** mudança no modo de código existente; novo script; alteração do contrato de saída
  (reusa o mesmo template e veredito).

## Design

- **Detecção de alvo:** se o alvo é um plano/spec em markdown (e não um diff/PR), carregar
  `plan-failure-catalog.md` **em vez** das stack addenda; pular stack-detection; manter
  `verification-protocol.md` e o rubric de veredito.
- **Âncora:** `arquivo:§seção` (ex.: `plan.md:§T3`) em vez de `file:line`. SARIF export não se aplica
  a planos (sem `file:line`); o relatório markdown é a saída.
- **10 categorias** (catálogo): (1) critério de aceite não-falsificável; (2) premissa não declarada;
  (3) ordering/dependência entre tasks; (4) rollback/idempotência ausente; (5) task sub-dimensionada
  que esconde um rewrite; (6) passo vago/não-verificável; (7) sem seam de verificação; (8) drift de
  contrato entre tasks; (9) recurso/permissão/secret não declarado; (10) premissa contradita pela
  realidade (→ ABANDON).
- **Veredito (planos):** ABANDON = meta/premissa declarada contradita por finding `confirmed`;
  REWORK = ≥1 `high` estrutural (replanejar / muda design cross-task); REFINE = `high` só local a uma
  task; GO = só `low`/follow-up.

## Tasks
- **T1** `assets/plan-failure-catalog.md` (catálogo + calibração + o que é "evidência" num plano).
- **T2** `SKILL.md`: seção `## Pre-mortem of a plan or spec` + entrada em Bundled files; description
  ganha trigger de plano/spec mantendo <1024 chars.
- **T3** Notas de âncora `file:section` no `premortem-md-template.md` e `verification-protocol.md`.
- **T4** `tests/fixtures/plan/{bug,clean}.md` + linha em `EVAL-RESULTS.md` (pisos recall/precision).
- **T5** Bump 2.1.0 (SKILL.md, sarif_export, plugin.json, marketplace.json, README badge) + README seção.

## Critérios de aceite
- [ ] description <1024 chars, 3ª pessoa, com trigger de plano/spec.
- [ ] SKILL.md <500 linhas; `pytest` 22/22 (sem regressão; modo é markdown-driven).
- [ ] `claude plugin validate .` passa; versão 2.1.0 consistente.
- [ ] Catálogo com 10 categorias; template/protocolo mencionam `file:section`.
