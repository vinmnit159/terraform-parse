**Part 1 – API Service**

Architecture
validators.py – Validation
renderer.py – Terraform generation
app.py – Flask API & I/O

Clean separation keeps business logic moduler.

API Endpoints

POST /api/v1/render
GET /healthz

Flow

Parse JSON → Validate → Generate HCL → Write file

Responses

201 – Success
400 – Invalid request
500 – I/O failure
Validation
Validates S3 names, ACLs, and regions.
Generates HCL using templates.
Uses AWS Provider 5.x resources.
Verified with terraform validate.

**Part 2 – Terraform**

Issues Found
Deprecated EKS module arguments.
Deprecated/public S3 ACL.
Hardcoded bucket names.
Weak variable validation.
Incorrect outputs.
Old provider/version.
No remote state.
No environment separation.

Changes made :
Upgraded EKS module.
Adopted Provider 5.x S3 resources.
Added encryption & versioning.
Parameterized bucket and cluster version.
Added variable validation.
Added backend template.
Added dev & prod tfvars.

Future
Remote state & locking
TFLint / Checkov
IRSA
Separate node groups
Terraform-managed VPC

**Part 3 – Helm**

Issues Found
YAML syntax errors.
Missing selectors.
Service/label mismatch.
Port mismatch.
Hardcoded values.
Ineffective HPA.
Missing probes.
Floating image tags.

Changes made :
Parameterized templates.
Added shared helpers.
Fixed selectors and ports.
Added requests, limits & probes.
Defaulted to ClusterIP.

Added terraform-parse service.
Validation
helm lint
helm template
helm install
kubectl get endpoints
In-cluster curl

**Part 4 – System Behavior**

terraform-parse
2 replicas
Gunicorn (2 workers)
Local file storage
400 on invalid input
500 on write failure


Current Gaps
No shared storage
No PDB
Single node group
No Cluster Autoscaler
No rate limiting
No circuit breaker

Future
S3 storage
PDB
Autoscaler/Karpenter
Multi-AZ nodes
Monitoring & alerts
Add testcases

**Part 5 – Approach & Tools**
References
Kubernetes Docs
Helm Docs
Terraform Docs
AI Assistance

Used Claude Opus 4.8 for:

Architecture discussion
Code generation
Code review
