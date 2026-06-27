# Análise completa da skill `premortem-code`

> Data: 2026-06-27 · Método: SDD (spec-driven) + análise multi-agente (2 agentes `Explore`)
> + verificação direta, calibrada pelos docs **mais recentes da Anthropic sobre skills**.

## Fontes de referência (Anthropic)

- [Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [`skill-creator/SKILL.md`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)
- [Equipping agents for the real world with Agent Skills](https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills)

## Veredito geral

Skill de **altíssima qualidade**. Estrutura uniforme (14 addenda de stack com template
idêntico), contrato de saída consistente entre template ↔ protocolo ↔ exportador SARIF,
SDD bem documentado com trilha de auditoria (2 rounds, 21 findings), e **nenhum problema de
segurança**. Medindo contra os docs oficiais, foram encontrados **2 erros reais**, **2 itens
stale** e algumas **oportunidades** — todos abaixo. Os erros e itens stale foram **corrigidos
neste branch**; as oportunidades ficam como backlog recomendado.

## Conformidade com os limites oficiais

| Regra Anthropic | Limite | `premortem-code` | OK? |
|---|---|---|---|
| `name`: lowercase/hífen, ≤64 ch, sem "claude"/"anthropic" | 64 | `premortem-code` (14) | ✅ |
| `description` ≤ 1024 ch | 1024 | 960 (após correção) | ✅ |
| `description` em 3ª pessoa | — | corrigido p/ "Conducts…" | ✅ (era ❌) |
| Corpo do SKILL.md < 500 linhas | 500 | 122 | ✅ |
| Referências 1 nível a partir do SKILL.md | — | todas diretas | ✅ |
| Triggers literais presentes na description | — | 5/5 preservados | ✅ |

## Achados

### 🔴 Erros confirmados (corrigidos neste branch)

1. **`SKILL.md:53` se contradizia.** Dizia *"These **6** are the shipped addenda"* logo acima de
   uma tabela de detecção com **14** linhas (e o README diz 14 stacks / 18 assets). Texto stale
   da época em que eram 6 stacks. → **Corrigido para "These 14 are the shipped addenda".**

2. **`description` não estava em 3ª pessoa.** Abria com imperativo *"Conduct an adversarial
   pre-mortem… assume… enumerate… drop… issue…"*. O best-practice é explícito: *"Always write in
   third person"* (a description é injetada no system prompt e voz inconsistente prejudica o
   discovery). → **Corrigido para 3ª pessoa** ("Conducts… assumes… enumerates… drops… issues…"),
   preservando os 5 trigger phrases literais; de quebra desceu de 966 → 960 chars.

### 🟠 Staleness (corrigido / mitigado)

3. **Spec original stale.** `docs/superpowers/specs/premortem-code-reconstruction.md` tinha
   critérios de aceite afirmando *"4 base + 6 stack = 10 assets"* como estado final — superado por
   `stack-addenda-increment.md` (14 stacks), sem marca de "superseded". Isso já chegou a confundir
   um agente de análise, que reportou erroneamente que o README estava desatualizado. → **Adicionado
   banner "SUPERSEDED / documento de auditoria"** no topo, apontando para o spec atual.

4. **`description` com margem apertada.** Estava em 966/1024 chars (94%). Ironicamente, o próprio
   `assets/stack-anthropic-skills.md` lista *"description cresce além de 1024"* como failure-mode.
   → A correção #2 abriu folga (agora 960; ~64 ch livres). Recomenda-se manter folga em edições
   futuras.

### 🟡 Oportunidades (backlog)

> **Atualização 2026-06-27:** itens 6, 7 e 8 endereçados no incremento
> `docs/superpowers/specs/ci-and-eval-increment.md` (branch `claude/readme-modernize-ppe60t`).
> Item 5 segue como decisão consciente de não-fazer.

5. **Convenção de pastas `references/` vs `assets/`.** O `skill-creator` distingue `references/`
   (docs carregados sob demanda), `assets/` (templates/ícones/fontes) e `scripts/` (executáveis).
   Aqui o catálogo, o protocolo de verificação, o subagent-prompt e os 14 `stack-*.md` são
   *references* mas vivem em `assets/`. Funciona (todas linkadas 1 nível a partir do SKILL.md), mas
   desvia da convenção atual. **Decisão: não reorganizar** — rename quebraria caminhos no SKILL.md,
   no installer e no próprio addendum, com baixo ganho funcional.

6. ✅ **TOC no `assets/fragility-catalog-core.md`** — feito: seção `## Contents` com as 10 categorias.

7. ✅ **CI** — feito: `.github/workflows/ci.yml` roda `pytest` (matriz 3.10–3.13) + `shellcheck` a cada
   push/PR, least-privilege e actions pinadas por SHA + Dependabot.

8. **Cobertura de teste.** (a) ✅ **E2E do CLI SARIF** — feito (`tests/test_sarif_cli_e2e.py`, valida o
   `.sarif.json` contra o schema OASIS). (b) ✅ **shellcheck** no installer agora roda no CI. (c) ✅ **Fixtures
   por stack** — adicionados 3 (postgres, agents-mcp, docker-k8s); os 11 stacks restantes seguem como backlog.

9. **Classificador de effort/mode** (novo) — ✅ feito: `assets/effort-classification.md` +
   `scripts/classify_effort.py` (advisory) recomendam `quick`/`standard`/`deep` por dificuldade/blast-radius.

## Itens verificados como corretos (não são problemas)

- README: "14 stacks / 18 assets" ✅ (4 base + 14 stack confirmados em disco) e "2 rounds, 21
  findings" ✅ (R1: 16 + R2: 5).
- Taxonomia de severidade (`high|medium|low`, sem "critical") e confiança
  (`confirmed|likely|speculative`) **consistentes** entre catálogo, protocolo, template e SKILL.md.
- Exportador SARIF 2.1.0 com campos de Code Scanning (`security-severity`, `partialFingerprints`,
  mapa de `level`); 8/8 testes passando.
- `install-premortem.sh`: `set -euo pipefail`, detecção de git robusta, `--prune` conservador, sem
  clobber. **Segurança: sem injeção de shell, sem path traversal, sem credenciais.**

## Mudanças aplicadas neste branch

| Arquivo | Mudança |
|---|---|
| `SKILL.md` | `description` → 3ª pessoa (achado #2); linha 53 "6" → "14" (achado #1) |
| `docs/superpowers/specs/premortem-code-reconstruction.md` | banner "SUPERSEDED" no topo (achado #3) |
| `.gitignore` | ignora `__pycache__/` + `*.pyc`; removidos 3 `.pyc` versionados (higiene) |
| `ANALYSIS.md` | este relatório (novo) |

Sem alterações em `assets/`, `scripts/`, `tests/` ou `install-premortem.sh`.
