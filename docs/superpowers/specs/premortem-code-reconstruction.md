# Spec — Reconstrução da skill `premortem-code`

Status: **AGUARDANDO APROVAÇÃO** (Fase 3 do dev-workflow). Sem implementação até aprovado.
Data: 2026-06-19 · Autor: Felipe (via Claude) · Repo: `~/projetos-2026/premortem-code`

## Objetivo

Reconstruir uma skill Claude Code `premortem-code` **equivalente em comportamento**
à original (artefato bespoke gerado no Claude.ai, não-público), a partir de **fontes
públicas verificadas** + o **contrato de saída** que sobreviveu no `premortems-README.md`
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

## Fontes verificadas (HTTP 200, lidas)

| Fonte | Uso | Licença (a confirmar na Fase 5) |
|---|---|---|
| `honnibal/claude-skills/pre-mortem.md.txt` | catálogo (10 cat.), formato post-mortem, calibração, workflow | verificar |
| `IgnatG/terraform-reviewer/.../sarif_export.py` | **padrão** do SARIF 2.1.0 (reimplementar, não copiar) | verificar |
| `karim-bhalwani/agentic-harness/.../fragility-catalogue.md` | formato standalone + "Hardening" | verificar |
| `stephenkiers/claude-helpers/expert-pre-mortem.md` | scan no `git diff`, assessment | verificar |
| `boshu2/agentops/skills/pre-mortem/SKILL.md` | escada de veredito, no-self-grading, kill-criteria | verificar |
| `premortems-README.md` (kit original) | **CONTRATO DE SAÍDA** (frontmatter + findings) | nosso |

## Arquitetura proposta

**Carregamento progressivo em 3 níveis** (best practice Anthropic):
- Nível 1 (sempre): `name` + `description` (a description otimizada, ≤1024 ch, já escrita).
- Nível 2 (ao disparar): `SKILL.md` ≤500 linhas — workflow + tabela de detecção + critérios de veredito + ponteiros "leia X quando Y".
- Nível 3 (sob demanda): assets carregados conforme o stack/etapa; `sarif_export.py` executado (código não entra no contexto).

**Contrato de saída** (fiel ao `premortems-README.md` — não inventar):
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

**Veredito (autoral — nenhuma fonte define; critérios explícitos):**
- `ABANDON` — a mudança não deveria existir como está (premissa quebrada). Raro.
- `REWORK` — ≥1 finding **high estrutural** (design, não pontual). Não mergear.
- `REFINE` — só ajustes pontuais (mediums, ou highs com fix local). Mergear após ajustar.
- `GO` — nenhum finding bloqueante; sobrou só low/tracked-for-followup.

**Modos:** `quick` (1 subagente, só high), `standard` (1–3 subagentes, high+medium),
`deep` (3 subagentes, high+medium+low+contradições). Default standard.

**Detecção de stack** (tabela no SKILL.md): gatilho → addendum. Carrega só os relevantes.

**Anti-falso-positivo** (`verification-protocol.md`): Hard gates por finding —
Anchor (ler símbolo inteiro, não só o hunk) → Evidence (citar `file:line`, não "olhei")
→ Severity (calibração honesta) → Format. Falhou um gate → omitir/rebaixar/virar pergunta.
Findings descartados vão para a seção "Dropped findings" (transparência).

## Task decomposition (commits atômicos)

1. **T1** — `fragility-catalog-core.md` (10 categorias + Future edit + Hardening; calibração). ~20min
2. **T2** — `verification-protocol.md` (Hard gates + por-tipo + "não reportar"). ~20min
3. **T3** — `subagent-prompt.md` (prompt do subagente adversarial; framing "já falhou"). ~15min
4. **T4** — `premortem-md-template.md` (contrato exato do README; força `file:line`). ~15min
5. **T5** — 6× `stack-*.md` (cada: descrição, Extends Category N, padrões, verification Qs, common false positives). ~30min cada → agrupar em 1–2 commits
6. **T6** — `scripts/sarif_export.py` (parse md → SARIF 2.1.0; pyyaml; valida `file:line`, warn+default). ~30min
7. **T7** — `SKILL.md` (frontmatter+description otimizada; workflow; tabela detecção; veredito). ~30min
8. **T8** — `README.md` + `LICENSE` + créditos de proveniência. ~15min
9. **T9** — Validação E2E: lint/parse, validar SARIF, instalar via `install-premortem.sh` corrigido, rodar em um diff real, conferir contrato. ~30min

## Dependências
- `pyyaml` (para `sarif_export.py` e parse de frontmatter)
- Python ≥3.10 (decisão da revisão: union `X | None`)
- `install-premortem.sh` corrigido (já em `~/premortem-review/fixed/`)

## Riscos + plano B
- **Licença das fontes.** Mitigação: **reimplementar** o `sarif_export.py` (não copiar) e
  **reescrever** o catálogo com palavras próprias (as categorias são ideias, não código);
  creditar as fontes no README. Plano B: se alguma fonte for restritiva, usar só como
  referência conceitual. → confirmar licenças no início da Fase 5.
- **Não é byte-a-byte a original.** Aceito pelo Felipe; objetivo é equivalência de comportamento.
- **Veredito autoral pode divergir do original.** Mitigação: critérios explícitos e ajustáveis.
- **SARIF location sem `file:line`** (bug conhecido do original). Mitigação: T4 força o formato + T6 valida.
- **SKILL.md > 500 linhas.** Mitigação: tudo que é detalhe vai para assets; SKILL.md só roteia.

## Estratégia de testes
- `python -c "import yaml; yaml.safe_load(frontmatter)"` no SKILL.md e no template.
- `sarif_export.py`: rodar num PREMORTEM de exemplo; validar com o one-liner de schema; testar caso de location não-estruturada (deve warn + default line 1).
- Instalar e confirmar contagem de assets (8 base+stack) e `claude /skills` lista a skill.
- E2E: rodar a skill (ou simular o fluxo) num diff real de um repo Python; conferir que o PREMORTEM gerado bate com o contrato.

## Critérios de aceitação ("pronto")
- [ ] `SKILL.md` ≤500 linhas, frontmatter YAML válido, `description` ≤1024 ch sem `<`/`>`.
- [ ] `assets/` com 4 base + 6 stack = 10 arquivos `.md`.
- [ ] `scripts/sarif_export.py` produz SARIF 2.1.0 válido e **avisa** em location não-`file:line`.
- [ ] Saída segue o contrato do `premortems-README.md` (frontmatter + findings + dropped).
- [ ] Instala via `install-premortem.sh` corrigido e aparece em `claude /skills`.
- [ ] E2E num diff real gera PREMORTEM com veredito coerente.
- [ ] README com créditos de proveniência + LICENSE; repo commitado.
- [ ] MEMORY.md atualizado.
