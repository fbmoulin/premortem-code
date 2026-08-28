# Stack addendum: AWS CDK

## When this loads
`aws-cdk-lib`/`@aws-cdk/*` (or `aws-cdk.*` Python packages) in dependencies; a
`cdk.json`; files named `*.cdk.ts`/`*.cdk.py` or constructs extending `Stack`,
`Construct`, calls to `new s3.Bucket(`, `Table(`, `Database(`, `removalPolicy`,
`account`/`region` in an `env`, or `CfnOutput`/`exportValue`/`Fn.importValue`.

## Extends
- Category 8 (load-bearing defaults) — `RemovalPolicy`/retention/encryption/deletion-protection defaults.
- Category 1 (implicit ordering dependencies) — logical-id stability, construct-id-derived resource identity.
- Category 7 (invisible invariants) — cross-stack export/import coupling held only by name.
- Category 4 (assumptions in data transformations) — env-agnostic vs hardcoded account/region.

## Failure-mode patterns
- **Construct-id / logical-id change replaces a stateful resource.** Renaming a construct id,
  re-nesting it, or moving it between stacks changes the CloudFormation logical id;
  CloudFormation then deletes the old resource and creates a new one. For a DynamoDB table,
  RDS instance, or S3 bucket this is silent data loss on the next `cdk deploy` (cat 1). Cite
  the construct whose id changed and its statefulness.
- **`RemovalPolicy.DESTROY` (or default) on a stateful resource.** A bucket/table set to
  `DESTROY` for a dev sandbox is reused in prod, or the default policy is relied on; a stack
  delete or replacement wipes the data with no recovery (cat 8). Stateful resources should be
  `RETAIN` with deletion protection; cite the policy line.
- **Replacement-triggering property edit.** Editing an immutable property — `partitionKey`,
  `engine`, KMS `encryptionKey`, VPC subnet layout — forces CloudFormation to replace the
  resource rather than update it (cat 1). The diff looks like a small edit; the deploy
  recreates and drops state. Run `cdk diff` and look for `(requires replacement)`.
- **Cross-stack reference locks the producer.** A `CfnOutput`/`exportValue` consumed by another
  stack via `Fn.importValue` cannot be changed or removed while the consumer references it;
  a future refactor that renames or deletes the export fails the deploy of the producer with a
  cross-stack-dependency error (cat 7). Cite the export and its importer.
- **IAM over-permissioning via `grant*`/wildcards.** A broad `grantReadWrite`, `addToPolicy`
  with `Resource: '*'`, or a managed policy attached "to make it work" widens blast radius;
  a later code path or a compromised function inherits more than intended (cat 8). Prefer
  least-privilege scoped grants; cite the wildcard or broad grant.
- **Hardcoded account/region in an "env-agnostic" stack.** A literal account id, region, or
  AZ string is baked in where the stack is otherwise deployed across environments; reusing the
  app in another account/region silently targets the wrong place or fails AZ lookups (cat 4).
  Cite the literal; prefer `Stack.of(this).account`/`region` or context.
- **Secret materialised in the synthesized template.** A plaintext password, token, or
  `SecretValue.unsafePlainText`/string interpolation lands in `cdk.out`/the CloudFormation
  template, which is stored and readable in S3/console (cat 8). Use `Secrets Manager` /
  `SSM SecureString` references resolved at deploy time; cite the inlined secret.

## Verification questions
- For each stateful resource (S3/DynamoDB/RDS/EFS): what is its `RemovalPolicy`, and is
  deletion protection / point-in-time recovery set? Cite the line.
- Has any construct id, nesting, or stack assignment of a stateful resource changed in this
  diff? Run `cdk diff`; cite any `(requires replacement)` or destroy/create on stateful types.
- Which properties edited here are replacement-triggering (partition key, engine, encryption
  key, VPC layout)? Cite each.
- Are there `Fn.importValue`/exported outputs consumed by another stack? Which renames/removals
  would break the producer deploy? Cite the export and consumer.
- Any `Resource: '*'`, broad `grant*`, or managed-policy attachment? Any hardcoded account/
  region/AZ? Any secret value present in synthesized output? Cite the line for each.

## Common false positives
- `RemovalPolicy.DESTROY` on a genuinely ephemeral resource (a log group, an auto-rebuildable
  cache, a CI sandbox bucket) is appropriate — not every DESTROY is data loss.
- A scoped `grantRead(bucket)` / `table.grantWriteData(fn)` that resolves to the resource ARN
  (not `'*'`) is least-privilege working as intended.
- An explicit `env: { account, region }` sourced from `process.env.CDK_DEFAULT_*` or context
  is the recommended way to pin a deploy target, not a hardcoded-environment bug.

---

Conceptually adapted from general knowledge of AWS CDK failure modes.
