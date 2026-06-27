# Spec — Reconstrução da skill `premortem-code`

> **⚠️ SUPERSEDED / documento de auditoria.** Este spec descreve o **milestone inicial de
> 6 stacks (10 assets)**. O estado atual do repo — **14 stacks / 18 assets** — é definido por
> [`stack-addenda-increment.md`](./stack-addenda-increment.md). Os critérios de aceite abaixo
> ("4 base + 6 stack = 10 assets", "6 shipped addenda") referem-se àquele milestone, **não** ao
> repo atual; mantidos aqui apenas como trilha histórica. Não reescrever o corpo.

Status: **REVISADO E PRONTO PARA FASE 5** — plan-review-cycle 2 rounds, 21 findings, todos
fechados, validador exit 0 (2026-06-19). Aguardando go do Felipe para execução.
Data: 2026-06-19 · Autor: Felipe (via Claude) · Repo: `~/projetos-2026/premortem-code`

## Objetivo

Reconstruir uma skill Claude Code `premortem-code` **equivalente em comportamento**
à original (artefato bespoke gerado no Claude.ai, não-público), a partir de **fontes
públicas verificadas** + o **contrato de saída** que sobreviveu no `.research/ORIGINAL-output-contract.md`
do kit original. Entregar instalável em `~/.claude/skills/premortem-code/`, versionada
e auditável.

**Por quê:** a skill original não existe em lugar nenhum acessível (confirmado por busca
ampla); só temos o "kit de implantação". Felipe quer a skill funcional para rodar
pré-mortem em PRs dos projetos (KCP, Kratos, etc.).

## Escopo

**Dentro:**
- `SKILL.md` (frontmatter + workflow + tabela de detecção de stack + lógica de veredito)
- `assets/`: `fragility-catalog-core.md`, `verification-protocol.md`, `subagent-prompt.md`, `premortem-md-template.md`
- `assets/stack-*.md` para os **6 stacks confirmados pelo Felipe**: `python-fastapi`, `postgres`, `redis-arq`, `qdrant`, `agents-mcp`, `docker-k8s`
- `scripts/sarif_export.py` (reimplementado, não copiado — ver Riscos/licença)
- `README.md` (humano), `LICENSE`, créditos de proveniência

**Fora (por enquanto):**
- Os outros 8 stacks (frontend, vercel, n8n, playwright, aws-cdk, anthropic-skills, finetuning, supabase) — moldes futuros, fora deste ciclo
- O loop de eval do skill-creator (otimização de description) — fase seguinte, opcional
- Integração CI (já temos `premortem.yml` corrigido no review)

## Fontes verificadas (HTTP 200, lidas) + licenças (T0 — 2026-06-19)

| Fonte | Uso | Licença | Decisão T0 |
|---|---|---|---|
| `honnibal/claude-skills/pre-mortem.md.txt` | catálogo (10 cat.), formato post-mortem, calibração, workflow | **MIT** | adaptar + atribuir |
| `IgnatG/terraform-reviewer/.../sarif_export.py` | padrão do SARIF 2.1.0 | **AGPL-3.0** 🔴 | **só referência conceitual** — não copiar/parafrasear; reimplementar do schema SARIF + docs GitHub |
| `karim-bhalwani/agentic-harness/.../fragility-catalogue.md` | formato standalone + "Hardening" | **MIT** | adaptar + atribuir |
| `stephenkiers/claude-helpers/expert-pre-mortem.md` | scan no `git diff`, assessment | **MIT** | adaptar + atribuir |
| `boshu2/agentops/skills/pre-mortem/SKILL.md` | escada de veredito, no-self-grading, kill-criteria | **Apache-2.0** | adaptar + atribuir + NOTICE |
| `.research/ORIGINAL-output-contract.md` (kit original; era `premortems-README.md`) | **CONTRATO DE SAÍDA** (frontmatter + findings) | nosso |

## Arquitetura proposta

**Carregamento progressivo em 3 níveis** (best practice Anthropic):
- Nível 1 (sempre): `name` + `description` (a description otimizada, ≤1024 ch, já escrita).
- Nível 2 (ao disparar): `SKILL.md` ≤500 linhas — workflow + tabela de detecção + critérios de veredito + ponteiros "leia X quando Y".
- Nível 3 (sob demanda): assets carregados conforme o stack/etapa; `sarif_export.py` executado (código não entra no contexto).

**Contrato de saída** (fiel ao `.research/ORIGINAL-output-contract.md` — não inventar):
```
---
generated, skill, mode, target, scope,
stack_detected: [...], addenda_loaded: [...],
verdict: GO|REFINE|REWORK|ABANDON,
risk_counts: {high, medium, low},
dropped_findings_count
---
## Detailed findings
### Finding N: <title>
**Category / Severity / Confidence / Location (file:line-line) / Mitigation verified absent**
#### Failure narrative
## Dropped findings (for transparency)
```

**Veredito (autoral; definição OPERACIONAL — R1-PRC008).** Cada veredito tem um
predicado mecânico que dois runs aplicam igual. Definições:
- Eixo **Confidence** (R2-PRC001), enum fixo: `confirmed | likely | speculative`.
  O `verification-protocol.md` (T2) traz um gate de atribuição de Confidence
  (espelhando o de Severity): `confirmed` exige evidência citada `file:line` de que a
  mitigação está ausente; `likely` = forte indício sem âncora exata; `speculative` =
  plausível mas não verificado (tende a virar Dropped). T6 e T9 asseram o enum.
- **structural** = o fix exige mudar design/interface pública/data-model/contrato
  cross-módulo, OU toca >1 módulo. **local** = qualquer fix confinado a 1 função/arquivo
  (R2-PRC002 — não só guard/validação). **Partição exaustiva:** todo `high` é structural
  ou local; um `high` que não é structural é tratado como local → REFINE.
- `ABANDON` — uma **premissa declarada** da mudança é contradita por um finding com
  `Confidence: confirmed`. Raro. Ex.: "esta migração é idempotente" mas há finding
  confirmado de não-idempotência.
- `REWORK` — ≥1 finding `high` **structural** (pela definição acima). Não mergear.
- `REFINE` — há findings mas todos os `high` são **local**, OU só `medium`/`low`.
  Mergear após ajustar.
- `GO` — nenhum finding bloqueante; só `low`/tracked-for-followup.

Cada veredito traz 1 exemplo de calibração no `verification-protocol.md` (inspirado
no `decision_rule` pré-registrado do boshu2/agentops) para os runs convergirem.

**Modos:** `quick` (1 subagente, só high), `standard` (1–3 subagentes, high+medium),
`deep` (3 subagentes, high+medium+low+contradições). Default standard.

**Detecção de stack** (tabela no SKILL.md): gatilho → addendum. Carrega só os relevantes.

**Anti-falso-positivo** (`verification-protocol.md`): Hard gates por finding —
Anchor (ler símbolo inteiro, não só o hunk) → Evidence (citar `file:line`, não "olhei")
→ Severity (calibração honesta) → Format. Falhou um gate → omitir/rebaixar/virar pergunta.
Findings descartados vão para a seção "Dropped findings" (transparência).

## Task decomposition (commits atômicos)

0. **T0 (hard-gate de licença — R1-PRC010)** — ANTES de T1/T6: registrar a licença de
   TODAS as fontes citadas (honnibal, terraform-reviewer, agentic-harness,
   stephenkiers, boshu2). Regra accept/reject: **permissiva** (MIT/Apache/BSD) →
   carregar o texto da licença + NOTICE no repo e creditar; **copyleft ou sem-LICENSE**
   → usar só como **referência conceitual** (sem paráfrase de estrutura/wording, sem
   ler-e-reescrever). Bloqueia o uso de fonte restritiva. ~20min
1. **T1** — `fragility-catalog-core.md` (10 categorias + Future edit + Hardening; calibração). ~20min
2. **T2** — `verification-protocol.md` (Hard gates + por-tipo + "não reportar"). ~20min
3. **T3** — `subagent-prompt.md` (prompt do subagente adversarial; framing "já falhou"). ~15min
4. **T4** — `premortem-md-template.md` (contrato exato do README; força `file:line`). ~15min
5. **T5** — 6× `stack-*.md` (cada: descrição, Extends Category N, padrões, verification Qs, common false positives). ~30min cada → agrupar em 1–2 commits
6. **T6** — `scripts/sarif_export.py` (parse md → SARIF 2.1.0; pyyaml; valida `file:line`,
   warn+default). `message.text` = título do finding + 1ª linha do Failure narrative
   (R2-PRC004, com teste de texto não-vazio). Label de parse casa o literal do contrato
   `Mitigation verified absent` (R2-PRC005), alinhado ao T4. ~60min
7. **T7** — `SKILL.md` (frontmatter+description otimizada; workflow; tabela detecção; veredito). ~30min
8. **T8** — `README.md` + `LICENSE` + créditos de proveniência. ~15min
9. **T9** — Validação E2E. (a) Instalar pelo método **canônico de skill**: `cp -r`
   da skill para `~/.claude/skills/premortem-code/` (R1-PRC001); adicionalmente,
   adicionar ao `install-premortem.sh` um **fallback flat** `$SOURCE_DIR/scripts/*.py`
   para o instalador seguir usável com layout flat; asserir inventário `SKILL.md +
   10 assets + 1 script`. (b) **Eval funcional com 2 fixtures sintéticos** (R1-PRC009 +
   R2-PRC003): (b1) diff com bug plantado conhecido (race check-then-act Python/Redis)
   que a skill DEVE pegar (recall); (b2) **fixture limpo** — diff correto sem fragilidade
   real, onde **orçamento**: 0 findings `high` e ≤2 findings espúrios totais (precisão).
   Os dois juntos são o piso falsificável de "equivalência de comportamento". (c) lint/parse YAML, validar SARIF (schema +
   campos do Code Scanning), conferir contrato. ~45min

## Dependências
- `pyyaml` (para `sarif_export.py` e parse de frontmatter)
- Python ≥3.10 (decisão da revisão: union `X | None`)
- `install-premortem.sh` corrigido (já em `~/premortem-review/fixed/`) — receberá
  fallback flat `$SOURCE_DIR/scripts/*.py` na T9 (R1-PRC001); instalação primária é
  `cp -r` canônico.

## Riscos + plano B
- **Licença das fontes.** Mitigação (reforçada — R1-PRC010): **T0 é hard-gate** que
  registra a licença de TODAS as fontes e decide accept/reject ANTES de T1/T6 —
  permissiva → texto da licença + NOTICE no repo + crédito; copyleft/sem-LICENSE → só
  referência conceitual (sem paráfrase de estrutura/wording). `sarif_export.py`
  reimplementado; catálogo reescrito com palavras próprias. Crédito-no-README sozinho
  é insuficiente e foi substituído por esta diligência.
- **Não é byte-a-byte a original.** Aceito pelo Felipe; objetivo é equivalência de comportamento.
- **Veredito autoral pode divergir do original.** Mitigação: critérios explícitos e ajustáveis.
- **SARIF location sem `file:line`** (bug conhecido do original). Mitigação: T4 força o formato + T6 valida.
- **SKILL.md > 500 linhas.** Mitigação: tudo que é detalhe vai para assets; SKILL.md só roteia.

## Estratégia de testes
- `python -c "import yaml; yaml.safe_load(frontmatter)"` no SKILL.md e no template.
- `sarif_export.py`: rodar num PREMORTEM de exemplo; validar com o one-liner de schema; testar caso de location não-estruturada (deve warn + default line 1).
- Instalar e confirmar inventário pós-install: `SKILL.md + 10 assets (4 base + 6 stack) + 1 script`; e `claude /skills` lista a skill.
- E2E: rodar a skill (ou simular o fluxo) num diff real de um repo Python; conferir que o PREMORTEM gerado bate com o contrato.

## Critérios de aceitação ("pronto") — VERIFICADOS 2026-06-19 (Fase 6)
- [x] `SKILL.md` 112 linhas, frontmatter YAML válido, `description` 881 ch sem `<`/`>`.
- [x] `assets/` com 4 base + 6 stack = 10 arquivos `.md`.
- [x] `scripts/sarif_export.py` produz SARIF 2.1.0 válido e **avisa** em location não-`file:line` (6/6 testes).
- [x] Saída segue o contrato do `.research/ORIGINAL-output-contract.md` (template T4).
- [x] Instala via `install-premortem.sh` (fallback flat) → SKILL.md + 10 assets + 1 script; skill aparece na lista.
- [x] E2E: 2 fixtures (bug→REWORK recall; limpo→REFINE, 0 high, falso-positivo dropado).
- [x] README + CREDITS + LICENSE (MIT) + NOTICE; 11 commits.
- [x] MEMORY.md atualizado.

## Round 1 Resolutions (emendas aplicadas)

Emendas ao spec/plan aprovadas no Lote A do plan-review-cycle (2026-06-19).

- **R1-PRC002 — severidade.** Severidade fixada em exatamente `{high, medium, low}`
  em todo o pipeline. Na reescrita do catálogo (T1), o nível "Critical" das fontes é
  **mapeado para `high`**. `risk_counts` permanece `{high, medium, low}` (contrato).
  T4 (campo Severity), T6 (`_LEVEL`/`security-severity` com 3 chaves) e T7 (veredito)
  referenciam só esses três.
- **R1-PRC003 — CLI do exporter.** Contrato fixo: `sarif_export.py --input PATH`
  grava `${PATH%.md}.sarif.json` ao lado do input e sai com código 0. T9 asserta a
  existência do arquivo irmão após uma run real.
- **R1-PRC004 — spec do parse.** T6 detalha: extrair labels `Category/Severity/`
  `Confidence/Location/Mitigation`; regex de location `^.+:\d+(-\d+)?$`; mapear range
  `a-b` → `region.startLine=a, endLine=b` (linha única → só startLine); **excluir** a
  seção "Dropped findings" dos `results`. Estimativa revista 30→~60min.
- **R1-PRC005 — campos do Code Scanning.** T6 implementa e a aceitação testa:
  `level` (high→error, medium→warning, low→note), `security-severity` em rule+result,
  `partialFingerprints` por result, `ruleId`/`ruleIndex`, `driver.rules[]`.
- **R1-PRC006 — test-first.** T6 reordenada: escrever `tests/test_sarif_export.py`
  primeiro (falhando) com casos (a) `file:line-line`→startLine/endLine; (b) location em
  prosa→warn + default line 1; (c) 2 findings preservam ordem; (d) Dropped excluído.
- **R1-PRC007 — stacks anunciados.** A `description` é aparada para os **6 stacks**
  confirmados; o SKILL.md (T7) tem tabela de detecção de 6 linhas + regra: "stack
  detectado sem addendum → usar só `fragility-catalog-core.md` e declarar isso no output".
- **R1-PRC012 — contagem.** Inventário pós-install fixado: `SKILL.md + 10 assets + 1 script`.
- **R1-PRC013 — critérios observáveis.** T5 exige as 5 seções nomeadas por addendum
  (descrição; Extends Category N; padrões; verification questions; common false positives).
  T3: o prompt abre com "assuma que esta mudança já falhou em produção". T1: as 10
  categorias nomeadas presentes.
- **R1-PRC014 — campo Hardening.** O template (T4) ganha sub-campo opcional `Hardening`
  por finding; o contrato é **estendido** (campo adicional, nenhum removido → compat).
- **R1-PRC015 — colisão de contagem.** T9 audita que `premortem.yml`/`TUTORIAL`
  corrigidos não asserem 14/18 fixos; README anota que contagens do TUTORIAL referem-se
  à original de 14 stacks, enquanto esta reprodução usa 6/10.

### Round 1 Resolutions — findings de juízo (opção A em todos)

- **R1-PRC001 (Critical).** Instalação primária = `cp -r` canônico de skill (T9);
  `install-premortem.sh` ganha fallback flat `$SOURCE_DIR/scripts/*.py`; T9 asserta
  inventário `SKILL.md + 10 assets + 1 script`.
- **R1-PRC008 (Major).** Veredito ganha definição **operacional** (structural vs local
  com predicado mecânico; ABANDON = premissa contradita por finding confirmed) + 1
  exemplo de calibração por veredito no `verification-protocol.md`. Ver §Arquitetura.
- **R1-PRC009 (Major).** T9 ganha eval funcional com **fixture sintético** (bug plantado
  conhecido que a skill DEVE pegar + orçamento de falso-positivo) como piso falsificável.
- **R1-PRC010 (Major).** **T0 = hard-gate de licença** sobre todas as fontes, antes de
  T1/T6 (accept/reject por tipo de licença). Ver §Task decomposition e §Riscos.

## Round 2 Resolutions (emendas aplicadas)

Aprovadas em bloco no Round 2 do plan-review-cycle (2026-06-19, opção "Aprovo todas").

- **R2-PRC001 — eixo Confidence.** Enum fixo `confirmed | likely | speculative` definido
  no §Veredito; gate de atribuição no `verification-protocol.md` (T2); ABANDON exige
  `Confidence: confirmed`; T6/T9 asseram o enum.
- **R2-PRC002 — partição exaustiva.** `local` redefinido como "qualquer fix confinado a
  1 função/arquivo"; default explícito: high não-structural → local → REFINE.
- **R2-PRC003 — orçamento de FP.** T9(b) ganha 2º fixture (limpo) + números: 0 high e
  ≤2 espúrios no fixture limpo (precisão), além do recall no fixture com bug.
- **R2-PRC004 — message.text.** T6 fixa `message.text` = título + 1ª linha do narrative,
  com teste de texto não-vazio.
- **R2-PRC005 — label.** T6 casa o literal `Mitigation verified absent` (alinhado ao T4).

## Plan Review Log

### Review Round 1

reviewer_model: claude-opus-4-8
reviewer_prompt: code-plan-reviewer@v0.4
date: 2026-06-19
spec_reviewed: .research/ORIGINAL-output-contract.md
plan_reviewed: docs/superpowers/specs/premortem-code-reconstruction.md
diverse_critics: true

#### Findings

##### Finding R1-PRC001: Installer never copies sarif_export.py (flat layout → 0 scripts)

status: Resolved
severity: Critical
location: Spec "Arquitetura proposta" / Dependências; Plan T9

reviewer_concern: |
  The fixed install-premortem.sh only copies scripts inside its Phase-3 block,
  which is discovered via fase3/scripts and has no flat $SOURCE_DIR/scripts
  fallback. The flat repo layout (SKILL.md, assets/, scripts/ at root) means an
  empirical install copies SKILL.md + all assets/*.md (10 assets, including stack
  addenda — those ARE caught) but ZERO scripts. sarif_export.py never lands.

why_it_matters: |
  After install there is no scripts/sarif_export.py in the skill dir, so CI
  (premortem.yml) hits file-not-found on the SARIF step, the whole Code-Scanning
  leg is dead, and the acceptance criterion "sarif_export.py produz SARIF válido"
  cannot pass via the documented install path. T9 is the only E2E gate and would
  green a half-installed skill.

decision: Resolved — opção A aprovada por Felipe (plan-review-cycle Round 1).

plan_changes_made: |
  Instalação primária via cp -r canônico (T9) + fallback flat scripts/*.py no install-premortem.sh.
  Propagação verificada (ver "Round 1 Resolutions — findings de juízo"):
  - [x] §T9: cp -r + asserir inventário 10 assets + 1 script
  - [x] §T9: adicionar fallback flat ao instalador
  - [x] §Dependências: nota do fallback

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC002: Severity taxonomy mismatch breaks the output contract

status: Resolved
severity: Critical
location: Spec "Contrato de saída" + "Veredito"; Tasks T1/T4/T6/T7

reviewer_concern: |
  The source catalogs (honnibal, agentic-fragility) define four severities
  Critical/High/Medium/Low, but the output contract's risk_counts has only
  high/medium/low and the verdict ladder references only "high". A Critical
  finding has no bucket and no verdict mapping.

why_it_matters: |
  T1 reworded from those sources will emit "Critical"; at T4/T7 it gets silently
  folded into high (destroying calibration) or a critical: key is added (making
  the frontmatter shape disagree with the contract = contract violation). The
  reimplemented sarif_export.py (modeled on terraform-sarif.py whose maps include
  critical) would diverge from the 3-bucket contract; any consumer parsing
  risk_counts for exactly high/medium/low breaks.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  Severidade fixada em {high, medium, low}; "Critical" das fontes mapeia para high.
  Propagação verificada (ver "Round 1 Resolutions" no spec):
  - [x] §Contrato de saída: risk_counts = {high, medium, low}
  - [x] T1: catálogo reescrito só com 3 níveis
  - [x] T4: campo Severity = high|medium|low
  - [x] T6: _LEVEL/security-severity com 3 chaves
  - [x] T7: veredito referencia só high/medium/low

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC003: Exporter CLI contract unspecified (signature + auto-named output)

status: Resolved
severity: Critical
location: Spec T6 + acceptance; Plan T6

reviewer_concern: |
  Both CI and the README invoke sarif_export.py --input <file> with no --output
  and no stdout capture, then read the result from ${PREMORTEM_FILE%.md}.sarif.json.
  The plan only says "parse md → SARIF" and never pins this signature or the
  auto-named sibling output path.

why_it_matters: |
  If the implementer builds stdout output, requires --output, or names the file
  differently, CI produces no file at the expected path, the upload is skipped
  (if sarif_file != ''), and the integration silently no-ops while "valid SARIF"
  technically passes. A contract the consumers already assume must be pinned.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  CLI fixada: --input PATH grava ${PATH%.md}.sarif.json (irmão), exit 0.
  Propagação verificada (ver "Round 1 Resolutions" no spec):
  - [x] §T6: assinatura + path de saída
  - [x] Critérios de aceitação: asserir arquivo irmão após run
  - [x] Estratégia de testes: caso saída no path esperado

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC004: The markdown→SARIF parse (the real work) is unspecified and underscoped

status: Resolved
severity: Major
location: Spec T6; Plan T6 (~30min)

reviewer_concern: |
  terraform-sarif.py serializes a typed FindingsReport object, but this exporter's
  input is markdown. None of the parsing is specified: stripping backticks from
  `src/x.py:88-115`, regexing the bold-labeled field block, mapping a range to
  startLine/endLine, choosing message.text, and excluding the Dropped-findings
  section.

why_it_matters: |
  Parsing the contract's finding format reliably (multiple findings, ranges vs
  single lines, optional dropped section) is the bulk of T6, not 30 minutes.
  Underscoping yields rework or a brittle exporter that mis-parses real premortems.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  T6 detalha o parse (labels, regex de location ^.+:\d+(-\d+)?$, range→startLine/endLine, exclui Dropped); estimativa 30→60min.

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC005: "Valid SARIF" criterion omits Code-Scanning-required fields

status: Resolved
severity: Major
location: Spec acceptance + "Estratégia de testes"; T6

reviewer_concern: |
  The only SARIF test is the schema-validation one-liner. GitHub Code Scanning
  additionally needs properties.security-severity (rule+result, for sorting),
  partialFingerprints (dedup/track across runs), the severity→level map
  (high→error, medium→warning, low→note), and a populated driver.rules[]. None
  are enumerated; the schema check won't catch their absence.

why_it_matters: |
  A SARIF file can pass schema validation yet render findings unsorted/untracked
  or unannotated in the PR — defeating the integration's purpose. Fixing only the
  file:line anchor still ships a degraded export.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  T6 implementa level/security-severity/partialFingerprints/ruleId/ruleIndex/driver.rules[]; aceitação testa as chaves.
  Propagação verificada (ver "Round 1 Resolutions" no spec):
  - [x] §T6: campos do Code Scanning
  - [x] Critérios de aceitação: teste asserindo as chaves num finding

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC006: No test-first/regression test for the exporter

status: Resolved
severity: Major
location: Spec "Estratégia de testes"; Plan gate after T6

reviewer_concern: |
  The plan does not write sarif_export.py with tests. T6's gate is a single manual
  smoke run after the code is written, not a test file, and not test-first.

why_it_matters: |
  Given the parse fragility, a one-shot smoke run won't protect against regressions
  when stack addenda or the template change. The promised prose-location→line-1
  fix (warn + default) is exactly the edge that needs a pinned test.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  T6 reordenada test-first: tests/test_sarif_export.py com 4 casos (file:line→region; prosa→warn+line1; ordem; Dropped excluído).

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC007: Description/detection advertise 14 stacks but only 6 addenda ship

status: Resolved
severity: Major
location: Spec "Detecção de stack" + Nível-1 description; SKILL.md (T7); Escopo

reviewer_concern: |
  The optimized description (sole always-loaded routing signal) enumerates ~14
  stacks and the kit's table has 14 rows, but this cycle builds only 6 stack-*.md.
  The plan doesn't constrain the SKILL.md table to the 6 built stacks.

why_it_matters: |
  On an n8n/Playwright/Vercel/CDK PR, Claude triggers, "detects" the stack, then
  finds no matching addendum and no table row → undefined/degraded behavior
  presented as complete. The description also sits at 991/1024 chars with no
  headroom. Scope ("Fora: 8 stacks") and the routing table contradict each other.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  description aparada para 6 stacks; SKILL.md com tabela de 6 linhas + fallback ao fragility-catalog-core.
  Propagação verificada (ver "Round 1 Resolutions" no spec):
  - [x] §Nível-1/description: lista = 6 stacks
  - [x] §Detecção de stack (T7): tabela 6 linhas + regra de fallback
  - [x] §Escopo: alinhado (fora: 8 stacks)

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC008: GO/REFINE/REWORK/ABANDON rubric is non-reproducible

status: Resolved
severity: Major
location: Spec "Veredito (autoral)"

reviewer_concern: |
  REWORK vs REFINE turns on "≥1 high estrutural (design) vs highs com fix local",
  a subjective distinction with no operational test; ABANDON ("premissa quebrada")
  is similarly undefined. The plan borrowed boshu2's verdict vocabulary but dropped
  its pre-registered decision_rule/kill condition.

why_it_matters: |
  The same diff can flip GO/REFINE/REWORK between runs (worse with subagent
  nondeterminism). CI hard-gates merge on REWORK/ABANDON, so an unreliable boundary
  makes the gate untrustworthy and "veredito coerente" uncheckable.

decision: Resolved — opção A aprovada por Felipe (plan-review-cycle Round 1).

plan_changes_made: |
  Veredito com definição operacional (structural=design/interface/data-model ou >1 módulo; local=guard no ponto; ABANDON=premissa contradita) + exemplo por veredito.
  Propagação verificada (ver "Round 1 Resolutions — findings de juízo"):
  - [x] §Arquitetura/Veredito: predicados mecânicos
  - [x] verification-protocol.md (T2): 1 exemplo de calibração por veredito

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC009: "Behavior-equivalence" has no oracle; functional eval deferred

status: Resolved
severity: Major
location: Spec Objetivo + Escopo "Fora" + Estratégia de testes; T9

reviewer_concern: |
  Behavior-equivalence is the stated goal, but the original is inaccessible (can't
  diff), the eval loop is out of scope, and the only functional check is "veredito
  coerente" on one diff — unfalsifiable. OPTIMIZATION names a concrete seed with a
  known outcome (KCP Sprint-5 ExecutionEngine race PR) that the plan skips.

why_it_matters: |
  The central success criterion cannot be verified by any acceptance test, and
  regressions when stacks 7-14 are added later go undetected. Needs at least one
  fixed-input/known-output functional assertion as the falsifiable floor.

decision: Resolved — opção A aprovada por Felipe (plan-review-cycle Round 1).

plan_changes_made: |
  T9 ganha eval funcional com fixture sintético (bug plantado + orçamento de FP) como piso falsificável de equivalência.
  Propagação verificada (ver "Round 1 Resolutions — findings de juízo"):
  - [x] §T9(b): fixture sintético + orçamento de falso-positivo
  - [x] §Estratégia de testes: caso funcional

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC010: Licensing mitigation checks existence, not terms

status: Resolved
severity: Major
location: Spec Riscos; Plan row 0

reviewer_concern: |
  Mitigation is "reimplement + reword + credit in README"; Task 0 is "curl LICENSE
  dos 3 repos-chave" (only 3 of 5+ sources), checking existence with no accept/reject
  rule. A README credit satisfies almost no real license (MIT/Apache need the
  license text + NOTICE; copyleft needs same-licensing; no LICENSE = all rights
  reserved). Reimplementing by reading-then-rewriting is not clean-room.

why_it_matters: |
  Legal exposure regardless of what each license turns out to be, with no gate to
  stop a restrictive source from being used or to enforce attribution correctly.

decision: Resolved — opção A aprovada por Felipe (plan-review-cycle Round 1).

plan_changes_made: |
  T0 vira hard-gate de licença sobre todas as fontes antes de T1/T6 (accept/reject por tipo).
  Propagação verificada (ver "Round 1 Resolutions — findings de juízo"):
  - [x] §Task decomposition: nova T0
  - [x] §Riscos: mitigação reforçada
  - [x] §Fontes: coluna licença a preencher na T0

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC011: Contract source filename mismatch (.research/ORIGINAL-output-contract.md vs on-disk)

status: Resolved
severity: Minor
location: Spec lines ~41/50/119; Plan T4

reviewer_concern: |
  Spec/plan repeatedly call the output contract .research/ORIGINAL-output-contract.md, but the file
  on disk is .research/ORIGINAL-output-contract.md. No .research/ORIGINAL-output-contract.md exists
  in the repo.

why_it_matters: |
  An implementer executing T4 greps for .research/ORIGINAL-output-contract.md, doesn't find it, and
  either guesses or stalls — wrong source → wrong frontmatter/findings shape.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  Todas as menções a premortems-README.md trocadas por .research/ORIGINAL-output-contract.md (spec + plan).

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC012: Asset-count self-contradiction (8 vs 10)

status: Resolved
severity: Minor
location: Spec "Estratégia de testes" ("8 base+stack") vs Critérios ("4 base + 6 stack = 10")

reviewer_concern: |
  The testing strategy says confirm asset count "8 base+stack" while the acceptance
  criterion says 4 base + 6 stack = 10.

why_it_matters: |
  T9 verifies the install by asset count; an "8" assertion fails against the correct
  10-file output, producing a false failure or masking a real one.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  Inventário pós-install fixado: SKILL.md + 10 assets + 1 script; "8" corrigido para 10.

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC013: Non-observable success criteria on T1/T3/T5

status: Resolved
severity: Minor
location: Plan T1 ("revisão visual"), T3 ("framing adversarial"), T5 ("5 seções")

reviewer_concern: |
  These gates are subjective or unenumerated: "framing adversarial" and "revisão
  visual" have no pass/fail; "5 seções" doesn't name which five.

why_it_matters: |
  The implementer can't self-verify completion and a reviewer can't confirm it;
  tasks get marked done on vibes and stack addenda may diverge in structure.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  T5 exige 5 seções nomeadas; T3 abre com 'assuma que já falhou em produção'; T1 exige as 10 categorias nomeadas.

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC014: Catalog "Hardening" content has no field in the output contract

status: Resolved
severity: Minor
location: Spec T1 ("Hardening") vs contract finding format; T4

reviewer_concern: |
  T1's catalog and the source post-mortem format carry per-finding "Hardening
  suggestions", but the contract's finding shape (Category/Severity/Confidence/
  Location/Mitigation verified absent + Failure narrative) has no hardening field.

why_it_matters: |
  The implementer must drop hardening content (losing useful behavior) or stuff it
  into the narrative (drifting from the contract). Left unspecified, T1 and T4
  disagree on whether findings carry remediation.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  Template (T4) ganha sub-campo opcional Hardening; contrato estendido (campo extra, nada removido).
  Propagação verificada (ver "Round 1 Resolutions" no spec):
  - [x] T4: sub-campo Hardening no finding
  - [x] T1: mantém hardening por categoria

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC015: 10-asset reality may collide with kit/CI/TUTORIAL counts (14 rows / 18 assets)

status: Resolved
severity: Minor
location: Spec Critérios; reuse of corrected premortem.yml + TUTORIAL

reviewer_concern: |
  The reproduction ships 10 assets / 6 stack rows; the original kit, its TUTORIAL,
  and CI reconcile to 18 assets / 14 table rows. The plan reuses the original
  premortem.yml.

why_it_matters: |
  If the corrected CI/TUTORIAL assert 14 rows / 18 assets, the 6-stack reproduction
  fails a count check or mismatches the detection table during E2E — a confusing
  failure at T9.

decision: Resolved — Lote A aprovado (plan-review-cycle Round 1, modo acelerado).

plan_changes_made: |
  T9 audita contagens fixas no premortem.yml/TUTORIAL; README nota 6/10 (repro) vs 14/18 (original).
  Propagação verificada (ver "Round 1 Resolutions" no spec):
  - [x] T9: check de inventário 6/10
  - [x] README: nota sobre contagens da original

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R1-PRC016: SKILL.md ≤500-line risk is adequately mitigated (no action)

status: No Plan Change
severity: Advisory
location: Spec Arquitetura + Riscos

reviewer_concern: |
  Positive-evidence note: with only 6 detection rows inline and all category/
  protocol/prompt detail pushed to assets via one-level pointers, the SKILL.md body
  fits comfortably under 500 lines. The real always-on budget pressure is the
  991/1024-char description (see R1-PRC007), not the body.

why_it_matters: |
  No failure mode here; flagging a change would be manufactured. Recorded only to
  close the sizing question raised in review and redirect budget scrutiny to the
  description.

decision: No Plan Change — observação de evidência positiva, sem modo de falha.

plan_changes_made: |

no_change_rationale: |
  Finding is a positive-evidence note confirming the SKILL.md body fits under 500 lines; there is no failure mode to fix. Budget pressure is the description char count, already addressed by R1-PRC007. Recorded and closed without plan change.

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

### Review Round 2

reviewer_model: claude-opus-4-8
reviewer_prompt: code-plan-reviewer@v0.4
date: 2026-06-19
spec_reviewed: .research/ORIGINAL-output-contract.md
plan_reviewed: docs/superpowers/specs/premortem-code-reconstruction.md
diverse_critics: false

#### Findings

##### Finding R2-PRC001: ABANDON keys on Confidence "confirmed", an axis no amendment pinned

status: Resolved
severity: Major
location: Spec "Veredito" (ABANDON clause); R1-PRC002/R1-PRC008 resolutions; verification-protocol gates

reviewer_concern: |
  ABANDON fires when a declared premise is contradicted by a "confirmed" finding, but
  "confirmed" is a Confidence value and Confidence is never enumerated anywhere (R1-PRC002
  pinned only Severity to {high,medium,low}). No gate assigns Confidence.

why_it_matters: |
  R1-PRC008 declared the verdict rubric mechanical so two runs converge, yet ABANDON's
  predicate rests on an unpinned value with no assignment rule. The two merge-blocking
  verdicts key on different axes (REWORK on pinned severity, ABANDON on unpinned
  confidence); a subagent can write any string, so ABANDON is non-reproducible — the
  exact defect R1-PRC008 claimed to fix.

decision: Resolved — Round 2 aprovado em bloco por Felipe.

plan_changes_made: |
  Enum Confidence {confirmed|likely|speculative}; gate no T2; ABANDON exige confirmed; T6/T9 asseram.
  Propagação (ver "Round 2 Resolutions"):
  - [x] §Veredito: eixo Confidence
  - [x] T2: gate de atribuição
  - [x] §Veredito: ABANDON usa Confidence: confirmed
  - [x] T6/T9: asserir enum

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R2-PRC002: structural/local is not exhaustive — a high can match neither

status: Resolved
severity: Major
location: Spec "Veredito" (structural/local definitions)

reviewer_concern: |
  structural is broad, but local is narrow ("guard/validation added at the finding point,
  1 function/file"). A high whose fix is a single-file change that is NOT a guard (reorder
  statements, off-by-one, change a load-bearing default, add a context manager) matches
  neither predicate.

why_it_matters: |
  REWORK keys on "≥1 high structural"; REFINE on "all highs local". An unclassifiable high
  satisfies neither → no verdict, or each run improvises a class, reintroducing the
  non-reproducibility R1-PRC008 closed. These are common catalog cases.

decision: Resolved — Round 2 aprovado em bloco por Felipe.

plan_changes_made: |
  local = qualquer fix em 1 função/arquivo; partição exaustiva (high não-structural → local → REFINE).
  Propagação (ver "Round 2 Resolutions"):
  - [x] §Veredito: definição de local + default

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R2-PRC003: T9 false-positive "budget" has no number and no negative corpus

status: Resolved
severity: Major
location: Spec T9(b); R1-PRC009 resolution; Estratégia de testes

reviewer_concern: |
  T9(b) requires a "declared false-positive budget" but gives no threshold and no
  clean/negative fixtures. The single planted-bug fixture tests recall only; a FP budget
  can only be measured against correct diffs, of which none are specified.

why_it_matters: |
  R1-PRC009 made the fixture the falsifiable floor for behavior-equivalence; as scoped the
  precision side is unmeasurable, so T9 can pass while emitting unlimited spurious findings.
  Recall checked, precision unverifiable.

decision: Resolved — Round 2 aprovado em bloco por Felipe.

plan_changes_made: |
  T9(b) ganha fixture limpo + orçamento (0 high, ≤2 espúrios) além do recall.
  Propagação (ver "Round 2 Resolutions"):
  - [x] §T9(b): 2º fixture + números
  - [x] §Estratégia de testes: precisão

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R2-PRC004: T6 never says which finding field becomes SARIF message.text

status: Resolved
severity: Minor
location: Spec T6 / R1-PRC004 resolution; terraform-sarif.py (message.text = evidence)

reviewer_concern: |
  R1-PRC004 enumerated labels, location regex, ranges, and Dropped-exclusion, but never
  said which markdown field maps to the required SARIF result.message.text. The contract has
  title, Mitigation, and Failure narrative; the reference uses evidence with no obvious
  counterpart.

why_it_matters: |
  message.text is required and renders as the PR annotation; with no mapping the implementer
  guesses, and the R1-PRC006 tests (region/order/Dropped) don't check message content, so a
  blank/wrong choice ships while tests pass.

decision: Resolved — Round 2 aprovado em bloco por Felipe.

plan_changes_made: |
  message.text = título + 1ª linha do narrative; teste de texto não-vazio.
  Propagação (ver "Round 2 Resolutions"):
  - [x] §T6: mapping message.text + teste

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19

##### Finding R2-PRC005: Parse label "Mitigation" vs contract "Mitigation verified absent"

status: Resolved
severity: Minor
location: Spec T6 / R1-PRC004 (label "Mitigation"); contract finding format ("Mitigation verified absent")

reviewer_concern: |
  R1-PRC004 lists the extraction label as "Mitigation", but the contract and spec line 61
  write "Mitigation verified absent:". The parse label set doesn't match the literal output
  label.

why_it_matters: |
  An exact-match regex on "Mitigation:" misses the field; prefix-match works by luck. This is
  the label drift R1-PRC004 meant to eliminate, and the four T6 tests don't cover this field.

decision: Resolved — Round 2 aprovado em bloco por Felipe.

plan_changes_made: |
  Label de parse = literal 'Mitigation verified absent', alinhado ao T4.
  Propagação (ver "Round 2 Resolutions"):
  - [x] §T6: label literal
  - [x] T4: mesma redação no template

no_change_rationale: |

human_approver: Felipe (fbmoulin)
approval_status: Approved
approval_date: 2026-06-19
