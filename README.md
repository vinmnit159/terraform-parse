<div align="center">
   <img src="/img/logo.svg?raw=true" width=600 style="background-color:white;">
</div>

# SRE Technical Take-Home Assignment : Terraform-Parse (Terraform + Helm)

Welcome to the Tripla SRE take-home assignment! 🧑‍💻 This exercise is designed to simulate a real-world scenario where you'll tackle challenges across infrastructure, platform engineering, and automation.

⚠️ **Before you begin**, please review the main [FAQ](/README.md#frequently-asked-questions). It contains important information, **including our specific guidelines on how to submit your solution.**

## Repo structure
- `terraform/` : Terraform code (intentionally imperfect) for an EKS cluster and an S3 bucket .
- `helm/` : A Helm chart (intentionally buggy) that deploys an API service .

## Candidate Tasks
### Create `Terraform-Parse` Service
1. Please Create a backend service to render an API request into terraform file
   (You can use any language/framework you’re comfortable with (e.g., Python/Flask, Node/Express, Go/Fiber). Keep it minimal.)
2. Service needs to receive rest api request (`POST` method) with certain payload.
    ```
    {
    "payload":{
        "properties":{
            "aws-region":"eu-west-1",
            "acl":"private",
            "bucket-name": "tripla-bucket"
        }
    }
    }
    ```
3. Parse this payload and and programmatically generate a valid Terraform configuration file (.tf) for S3 bucket creation. Resources created should at least include:
    - provider
    - aws_s3_bucket
    - aws_s3_bucket_acl
4. Please put your code to folder `terraform_parse_service`

### Infrastructure (Terraform)
5. You have provided a set of Terraform code to create an EKS. Please review the code, identify issues or design flaws.
6. Adjust or refactor be safe and maintainable for multiple environments.

### Platform (Kubernetes + Helm)
7. You are provided a set of Helm code. Please review and deploy `Terraform-Parse` service into a Kubernetes cluster using the provided Helm setup (local kind/minikube is fine).
8. Debug and fix if you find services don't route properly.
9. Improve other aspects as you see fit.

## Minimum Deliverables
1.  A link to your Git repository containing the complete solution.
2.  Clear instructions in the `README.md` on how to build, test, and run your service.
3. `NOTES.md` with explanations for API service creation, Terraform fixes, Helm fixes, multi-env thoughts, and any AI usage.

---

# Solution

## 1. terraform_parse_service (Python/Flask)

### Run locally
```bash
cd terraform_parse_service
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
flask --app app run --port 5000
```

### Run with Docker
```bash
cd terraform_parse_service
docker build -t terraform-parse:0.1.0 .
docker run --rm -p 5000:5000 terraform-parse:0.1.0
```

### Try it
```bash
curl -X POST localhost:5000/api/v1/render \
  -H 'Content-Type: application/json' \
  -d '{"payload":{"properties":{"aws-region":"eu-west-1","acl":"private","bucket-name":"tripla-bucket"}}}'

curl localhost:5000/healthz
```
Response includes the rendered `.tf` content and also writes it to `terraform_parse_service/output/<bucket-name>.tf`.

## 2. terraform (EKS + S3)

Requires an existing VPC and at least two subnet IDs (see `terraform/envs/*.tfvars` — replace the placeholder `vpc-`/`subnet-` IDs with real ones for your account).

```bash
cd terraform
terraform init
terraform validate
terraform fmt -check -recursive
terraform plan -var-file=envs/dev.tfvars   # or envs/prod.tfvars
```

No remote backend is configured (commented template in `versions.tf`) since there's no live AWS account behind this assignment.

## 3. helm (frontend + backend + terraform-parse)

Local deploy on kind:

```bash
# 1. build and load the service image into the cluster
cd terraform_parse_service
docker build -t terraform-parse:0.1.0 .
kind create cluster --name tripla
kind load docker-image terraform-parse:0.1.0 --name tripla

# 2. lint/render check, then install
cd ../helm
helm lint .
helm template . > /dev/null   # renders cleanly
helm install tripla . --wait --timeout 3m
```

### Verify

```bash
kubectl get pods
kubectl get endpoints        # every service should list at least one IP:port

kubectl run curl-test --rm -i --restart=Never --image=curlimages/curl:8.11.0 -- sh -c '
  curl -s backend-svc:8080;
  curl -s -o /dev/null -w "frontend: %{http_code}\n" frontend-svc:80;
  curl -s -X POST terraform-parse:8080/api/v1/render \
    -H "Content-Type: application/json" \
    -d "{\"payload\":{\"properties\":{\"aws-region\":\"eu-west-1\",\"acl\":\"private\",\"bucket-name\":\"tripla-bucket\"}}}"'
```

Teardown: `kind delete cluster --name tripla`

See `NOTES.md` for the issues found in the original Terraform/Helm code and how each was fixed.
