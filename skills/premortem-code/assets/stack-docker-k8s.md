# Stack addendum: Docker / Kubernetes

## When this loads
`Dockerfile`, `docker-compose.y*ml`, a `k8s/` directory, or Kubernetes YAML kinds
(`Deployment`, `Service`, `StatefulSet`, `Ingress`, etc.).

## Extends
- Category 8 (load-bearing defaults) — tags, resource limits, replicas, env.
- Category 9 (resource lifecycle) — startup/shutdown, volumes, connections.
- Category 1 (ordering) — service/dependency readiness ordering.

## Failure-mode patterns
- **Mutable image tag.** `image: app:latest` (or no digest) → a redeploy pulls a
  different image than tested; rollbacks are not reproducible (cat 8/10).
- **No resource limits / requests.** A container without limits can starve neighbours
  or get OOM-killed unpredictably under load (cat 8).
- **Missing/incorrect health probes.** No `readinessProbe` → traffic routed before the
  app is ready (cat 1); no `livenessProbe` or a too-aggressive one → crash loops.
- **No graceful shutdown.** App ignores SIGTERM / has no `terminationGracePeriod`
  handling → in-flight requests/jobs dropped on rollout (cat 9).
- **State in an ephemeral container.** Writing data to the container FS / an `emptyDir`
  assumed durable → lost on restart/reschedule (cat 9). Needs a PVC.
- **Secret/config baked into the image or compose file** (cat 8; security).
- **`depends_on` assumed = ready.** Compose `depends_on` waits for *start*, not
  readiness; the app connects before the DB accepts connections (cat 1).
- **Single replica assumed for correctness.** Logic relying on one instance breaks when
  `replicas > 1` (in-memory locks/caches/schedulers) (cat 2/6).

## Verification questions
- Are images pinned by tag+digest, not `latest`?
- Do containers set resource requests/limits and correct readiness/liveness probes?
- Is SIGTERM handled with a grace period? Is durable state on a PVC, not the container FS?
- Does any logic assume a single replica while the Deployment can scale?

## Common false positives
- `latest` in a local dev compose (not the prod manifest) is acceptable.
- A stateless container writing only temp scratch to `emptyDir` is fine.
- A job/CronJob that is meant to be a singleton and is configured as one is not a finding.
