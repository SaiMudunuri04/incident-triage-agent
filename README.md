# Incident triage agent

[Architecture](docs/architecture.md) · [Operations runbook](docs/operations.md) · [Helm chart](k8s/helm/incident-triage-agent/) · [Argo CD application](k8s/argocd/application.yaml)

An independent service for bounded, read-only tool orchestration. This repository contains executable source, tests,
a container, Helm release, Argo CD application, and a CI workflow that builds an
immutable GHCR image after tests pass. It is a reference implementation; it has not
been deployed to a user's AWS account or Kubernetes cluster.

## Start here

**Problem:** assist incident triage without allowing an agent to take unsafe actions. **What this demonstrates:** a bounded plan-act-observe loop, read-only tools, an action allowlist, and summaries tied to successful observations. **Inspect first:** [`docs/architecture.md`](docs/architecture.md), [`src/service/app.py`](src/service/app.py), and the safety tests.

## Run

```sh
python -m pip install -e '.[test]'
python -m pytest -q
ruff check .
helm lint k8s/helm/incident-triage-agent --strict
uvicorn service.app:app --reload
```

`/health/live` checks the process. `/health/ready` checks required local resources. Responses include a request ID and no-store/nosniff headers; JSON request logs omit bodies and query strings.
Configure data, model artifacts, and inference endpoints before serving traffic.

## Delivery

The workflow tests pull requests, then builds/pushes an image to GHCR on `main` and
updates the Helm image tag to the tested commit. Argo CD follows the single chart at [`k8s/helm/incident-triage-agent/`](k8s/helm/incident-triage-agent/).
Install `k8s/argocd/application.yaml` in a cluster with Argo CD, set environment-specific
Helm values, provide secrets through a cluster secret manager, and make the package
pullable by the cluster. Model/data volumes are configured through `volumes` and
`volumeMounts`; use `envFromSecretName` for credentials. The workflow does not
provision AWS or a cluster.

`.env.example` contains placeholders only. Never commit credentials or private data.

## Configure and serve

Mount approved Markdown runbooks and a JSON object of read-only numeric metrics. The planner can only `search_runbook`, `read_metric`, or `finish`; unrecognized actions produce an audit error. `finish` must cite successful tool observations as `step:N`, and a strict step budget bounds the loop. The system never changes infrastructure.

```sh
RUNBOOK_ROOT=/path/runbooks METRICS_PATH=/path/metrics.json LLM_BASE_URL=https://your-model.example/v1 LLM_MODEL=your-model uvicorn service.app:app --host 127.0.0.1
```

Keep runbooks and metrics read-only and supply `LLM_API_KEY` from a secret manager. The final summary is a suggestion requiring human review, not an automated remediation. No real incident data or live inference service is included.
