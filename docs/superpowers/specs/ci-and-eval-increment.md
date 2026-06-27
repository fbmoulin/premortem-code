# Spec — Incremento de CI, testes E2E, TOC e classificador de effort

Status: **EM EXECUÇÃO** (aprovado pelo Felipe). Branch: `claude/readme-modernize-ppe60t`.
Data: 2026-06-27 · Método: SDD + deep-research (24 fontes, 23 claims confirmados, 2 refutados) + pre-mortem do próprio plano.

## Objetivo

Endereçar o backlog de [`ANALYSIS.md`](../../../ANALYSIS.md) com 5 entregáveis, todos aditivos e sem breaking change:
CI (`pytest`+`shellcheck`), TOC no catálogo de fragilidades, teste E2E do CLI SARIF, fixtures de eval para 3 stacks,
e um classificador de effort/mode fundamentado em pesquisa.

## Decisões (Felipe)
1. Fixtures de eval: **3 stacks** (postgres, agents-mcp, docker-k8s); resto = backlog.
2. Classificador: **heurística markdown + `scripts/classify_effort.py` opcional** (com testes).
3. Upload SARIF: **só documentar o padrão**; CI core = pytest + shellcheck.

## Fundamentação (deep-research, citações)

| Tópico | Recomendação verificada | Fonte |
|---|---|---|
| Pinning de actions | full commit SHA (ataque tj-actions, mar/2025) + Dependabot | wiz.io; docs GitHub |
| Permissões | `permissions: {}` no workflow; conceder por job; só SARIF com `security-events: write` | wiz.io; codeql-action |
| upload-sarif | `github/codeql-action/upload-sarif@v4` (v3 deprecando dez/2026) | codeql-action README |
| shellcheck | `ludeeus/action-shellcheck` (`scandir`/`severity`/`SHELLCHECK_OPTS`) | ludeeus/action-shellcheck |
| Validar SARIF | schema OASIS 2.1.0 é draft-04; exigir `version=="2.1.0"`+`runs`; `Draft4Validator` | oasis-tcs/sarif-spec |
| Effort tiering | funil tipo RADAR (gates baratos → risco por blast-radius) + regras por path tipo Danger | arxiv 2605.30208; danger.systems |
| Effort por dificuldade | compute-optimal test-time scaling: esforço proporcional à dificuldade | Snell 2024 (hf 2408.03314) |

**Refutado (NÃO citar):** métricas de segurança do RADAR (revert 1/3, PI 1/50); bloco exato de perms private-repo do differential-shellcheck.

## SHAs pinados (resolvidos via API GitHub, 2026-06-27; Dependabot mantém)
- `actions/checkout` v7.0.0 → `9c091bb21b7c1c1d1991bb908d89e4e9dddfe3e0`
- `actions/setup-python` v6.3.0 → `ece7cb06caefa5fff74198d8649806c4678c61a1`
- `ludeeus/action-shellcheck` 2.0.0 → `00cae500b08a931fb5698e11e79bfbd38e612a38`

## Tasks (1 task = 1 commit)

- **T1** `.github/workflows/ci.yml` + `.github/dependabot.yml` + `requirements-dev.txt`. Jobs `test` (matriz 3.10–3.13)
  e `shellcheck`. `permissions: {}` default; `contents: read` por job. Cache pip apontado para `requirements-dev.txt`.
- **T2** Documentar (README/SKILL) o padrão opcional de upload SARIF a Code Scanning (codeql-action@v4, perms mínimas).
- **T3** `## Contents` no `assets/fragility-catalog-core.md` (índice das 10 categorias).
- **T4** `tests/test_sarif_cli_e2e.py`: `sx.main(["--input", p])` → valida `.sarif.json` (version/runs sempre; schema sob
  `importorskip`) contra `tests/fixtures/sarif-schema-2.1.0.json` bundlado; atribuição OASIS em NOTICE/CREDITS.
- **T5** `tests/fixtures/{postgres,agents-mcp,docker-k8s}/{bug,clean}.*` + linhas em `EVAL-RESULTS.md` (pisos recall/precision).
- **T6** `assets/effort-classification.md` + seção `## Mode selection` no SKILL.md + `scripts/classify_effort.py` (advisory, conservador) + testes.
- **T7** Atualizar `ANALYSIS.md` (itens de backlog → done).

## Pre-mortem do plano (auto-aplicado — veredito REFINE)

| Cat | Fragilidade | Mitigação |
|----|-------------|-----------|
| 8 | `cache: pip` sem requirements → CI vermelho | `requirements-dev.txt` + `cache-dependency-path` |
| T0 | schema OASIS sem atribuição | proveniência em NOTICE/CREDITS |
| 5 | `importorskip` dá falso-verde | asserts version/runs sempre; só schema sob guard |
| 1/7 | input do teste diverge do template | reusar `SAMPLE` de `test_sarif_export.py` |
| 8 | shellcheck pega SC pré-existente | `shellcheck install-premortem.sh` rodado local → **CLEAN** ✓ |
| 4/8 | classifier rebaixa diff sensível | viés conservador, advisory, ≥standard em paths sensíveis |
| 10 | Draft4Validator acoplado à versão | fixar `jsonschema<5` |
| 5 | EVAL-RESULTS como verdade exata | pisos de recall/precision |

## Critérios de aceite
- [ ] `pip install -r requirements-dev.txt && python -m pytest tests/ -q` verde (inclui E2E).
- [ ] `shellcheck install-premortem.sh` limpo.
- [ ] Actions pinadas por SHA; `permissions: {}`; nenhum job com escrita.
- [ ] TOC, E2E SARIF, 3 fixtures por stack, classificador entregues.
- [ ] description do SKILL.md <1024 chars; sem breaking change; `ANALYSIS.md` atualizado.
