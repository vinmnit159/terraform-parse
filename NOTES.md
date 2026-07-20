- Part 1 (API Service): 
## Architecture & Design Philosophy
The service uses a decoupled, three-file architecture to isolate side effects from pure business logic:

* validators.py: Pure input validation, zero input/output (I/O).
* renderer.py: Pure HCL template generation, zero I/O.
* app.py: HTTP framework layer (Flask), handles status codes, JSON parsing, and logging.

This division ensures that validation and rendering are pure functions. They are easily unit-tested without spinning up an HTTP test client, presenting a design that separates framework dependencies from business logic.
## API Contract & Execution Flow
The service exposes POST /api/v1/render for payload processing and GET /healthz for Kubernetes probes. The execution flow includes:

   1. Ingestion: Parses input using request.get_json(silent=True). Malformed JSON returns a 400 error instantly.
   2. Validation: Runs validate_payload(body). Failures raise a ValidationError, logged at INFO and returned as a 400 error with specific details.
   3. Rendering: Executes render_s3_tf to build the HCL string.
   4. I/O Handling: Writes the string to output/<bucket-name>.tf (configurable via OUTPUT_DIR for Docker). A successful run returns a 201 status with both the filename and raw content. I/O failure (e.g., disk full) returns a 500 status cleanly without crashing the process.

## Validation & Generation Strategy
The application enforces strict validation at the API boundary to catch errors before they surface downstream during a terraform apply:

* Validates bucket names against exact S3 constraints (3–63 characters, no consecutive dots, no IP shapes).
* Checks ACLs against official AWS canned-ACL enums and matches regions to standard patterns.
* Uses explicit string templates (str.format) for HCL generation, avoiding heavy AST libraries since strict upstream validation eliminates injection risks.
* Implements AWS Provider 5.x standards by splitting the bucket, ownership controls, and ACLs into distinct resources. It uses an explicit depends_on statement to handle AWS's default bucket protections properly.
* Runs terraform validate in temporary directories during testing to prove semantic correctness.


- Part 2 (Terraform): 
- Issues found:

EKS module pinned 19.0.0 used node_groups arg — renamed to eks_managed_node_groups in v18+. Unknown args are silently ignored, so apply succeeds but creates zero worker nodes. Worst kind of bug: no error, just a dead cluster.
aws_s3_bucket.acl = "public-read" — deprecated inline syntax (removed in provider v5) and a security flaw (world-readable bucket).
Hardcoded bucket name — S3 names are globally unique, so multi-env deploys would collide.
vpc_id/subnet_ids defaulted to ""/[] — passes plan, fails cryptically deep in the module at apply.
Wrong output (cluster_id labeled cluster_name), hardcoded EOL cluster_version = "1.25", provider pinned to old ~> 4.0, no state backend, no env separation.

Approach: 
bumped module to ~> 20.0 with correct eks_managed_node_groups schema; replaced the ACL with aws_s3_bucket_acl + ownership-controls + public-access-block 
+ versioning + encryption; parameterized bucket name with ${project}-${environment}; removed the empty defaults and added validation blocks on vpc_id/subnet_ids so 
+ bad input fails at plan-time with a clear message; parameterized cluster_version; fixed the output; added a commented backend "s3" block (no live account to
+ migrate state into); added envs/dev.tfvars and envs/prod.tfvars for multi-env, single root module.

Could still be enhanced: actual remote state + locking once an AWS account exists; tflint/checkov in CI; IRSA setup for pod-level IAM; 
separate node groups for system vs. workload pods; VPC itself is assumed pre-existing rather than managed here — worth revisiting if Tripla wants 
full network lifecycle in Terraform too.

- Part 3 (Helm): 
- Problems found:

backend-deployment.yaml had a stray leading \ plus wrong indentation — chart failed to render entirely.
Both Deployments missing required spec.selector.matchLabels — API server rejects on apply.
Routing bug (task 8): frontend pods labeled app: frontend-app, but the Service selector was app: frontend — zero matching endpoints, every request refused, despite pods showing Running.
Second routing layer: http-echo listens on 5678 by default, but its Service targeted 8080 — labels alone weren't enough, ports had to agree too.
values.yaml was entirely disconnected — every template hardcoded image/port/replicas, defeating the point of Helm.
HPA present but useless: no resource requests on the backend, so CPU utilization (usage÷request) was undefined — autoscaling silently did nothing.
LoadBalancer default (hangs Pending forever on kind), :latest tags, no probes.

Approach: 

Rewrote all templates to pull from .Values; added a shared _helpers.tpl so Deployment selector, pod labels, and Service selector all derive from one 
source and can't drift apart again; fixed the port mismatch; added resource requests/limits and readiness/liveness probes everywhere; defaulted Service type to
ClusterIP; pinned image tags. Added a new terraform-parse Deployment+Service for the built service.

Validation: helm lint → helm template (renders clean) → real deploy on kind (helm install --wait) → kubectl get endpoints confirmed non-empty for all three services
→ in-cluster curl to frontend, backend, and terraform-parse all returned correct responses, proving routing actually works end-to-end, not just "looks right on paper."

- Part 4 (System Behavior): 
terraform-parse service: 2 replicas, gunicorn 2 workers each — fine for bursty internal traffic, not high sustained QPS. 
- Each request writes output to local pod disk; with multiple replicas and no shared volume, generated files land on whichever pod served the request — invisible 
- from the other. At scale this needs S3 (or just drop the file write, return content only — simpler fix). Bad payload fails fast (400) before any expensive work; 
- disk-write failure returns 500 but doesn't crash the process.

backend/frontend: HPA scales backend 1→5 on CPU, but http-echo is stateless and trivial — real load risk is elsewhere (e.g. terraform-parse doing actual work). 
No PodDisruptionBudget yet, so a node drain during a rolling deploy could take all replicas down simultaneously if unlucky.

EKS layer: single managed node group, one instance type — a spot/capacity issue takes out everything. No multi-AZ node group spread enforced 
explicitly (relies on subnet_ids/module defaults). Cluster autoscaler not configured — HPA can add pods but nothing adds nodes.

Failure scenarios not yet handled: no circuit breaker if terraform-parse calls anything external in future; no rate limiting on the API (one client could hammer it);
no persistent volume backup story.

Long-term resilience: add PDBs, cluster-autoscaler/Karpenter, multi-AZ node groups, move output storage to S3, add rate limiting + request timeouts, 
Prometheus metrics + alerts (error rate, latency, HPA saturation) instead of just logs, and chaos-test node loss / pod eviction before calling it production-ready.

- Part 5 (Approach & Tools): 
- Used K8s documentations ,
- Helm and Terraform documentations . 
- Also used claude opus 4.8 in solution architecture discussion , code generation and review of my own code as well .
- 
- 