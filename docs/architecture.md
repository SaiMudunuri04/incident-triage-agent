# Incident triage agent architecture

## Request and model path

Incident description → bounded planner loop → read-only runbook/metric tools → audited observations → step-cited summary or step limit

## Boundaries

- **Input:** Approved Markdown runbooks and a JSON metrics object. Tool actions are allowlisted to search, read, and finish.
- **Runtime:** `LLM_BASE_URL` and `LLM_MODEL` select a local or HTTPS planner. `finish` must cite successful observations as `step:N`.
- **Failure behavior:** Missing tool data makes readiness 503; missing endpoint configuration makes `/triage` return 503. Unrecognized actions are logged as rejected observations.

The FastAPI process exposes `/health/live` for process liveness and `/health/ready` for local prerequisites. Each HTTP response carries a generated `X-Request-ID`, `Cache-Control: no-store`, and `X-Content-Type-Options: nosniff`. JSON request logs record method, path, status, request ID, and duration, never request bodies, query strings, credentials, or user data. Logs are local process telemetry, not a claim of production monitoring.

The [single Helm chart](../k8s/helm/incident-triage-agent/) provides rolling updates, probes, resource bounds, security contexts, optional HPA and NetworkPolicy, and a PDB. [Argo CD](../k8s/argocd/application.yaml) points to that chart. Values need environment review before deployment, especially image pull access, ingress peers, external inference egress, and artifact mounts.

## Limits

The agent does not change infrastructure. Step citations identify observations but do not guarantee the summary is correct; a human must review advice.
