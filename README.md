# NimbusKart Cost Janitor

## Overview

NimbusKart Cost Janitor is a local cloud cost hygiene and automation project built with Terraform, LocalStack, Python, and GitHub Actions.

The project creates a small AWS-like environment locally using LocalStack and then runs a Python Cost Janitor script to detect unused or risky cloud resources. The goal is to show how a company like NimbusKart can identify cloud waste before it becomes expensive in production.

The Janitor checks for:

- Unattached EBS volumes
- Stopped EC2 instances older than 14 days
- Unused Elastic IPs
- Missing required tags
- Protected resources that should not be deleted automatically

No real AWS account is required. Everything runs locally through LocalStack.

---

## Architecture

The Terraform stack creates the following local AWS-style resources:

- VPC with CIDR `10.20.0.0/16`
- Two public subnets
- Internet Gateway
- Public route table
- Security group
- Two EC2 instances
- S3 bucket with versioning enabled
- One known unattached EBS volume for Janitor testing

High-level flow:

~~~text
Terraform -> LocalStack AWS services -> Python Janitor -> JSON/Markdown reports -> GitHub Actions
~~~

The known unattached EBS volume is intentionally created so the Janitor has a real cost hygiene issue to detect.

---

## Repository Structure

~~~text
.
├── README.md
├── DESIGN.md
├── SUBMISSION.md
├── terraform/
├── janitor/
├── .github/workflows/cost-janitor.yml
├── docs/walkthrough.md
└── samples/
    ├── report.example.json
    └── report.example.md
~~~

---

## Prerequisites

Install these tools:

- Docker
- Terraform
- Python 3.12+
- Git

This project was tested using:

~~~text
localstack/localstack:3.8.1
~~~

---

## Local Setup

Start LocalStack:

~~~bash
docker run --rm -d -p 4566:4566 --name localstack localstack/localstack:3.8.1
~~~

Check that it is running:

~~~bash
docker ps
~~~

Set fake AWS credentials:

~~~bash
export AWS_ACCESS_KEY_ID=test
export AWS_SECRET_ACCESS_KEY=test
export AWS_DEFAULT_REGION=us-east-1
~~~

---

## Deploy Infrastructure

~~~bash
cd terraform
terraform init
terraform validate
terraform apply -auto-approve
~~~

Check outputs and resources:

~~~bash
terraform output
terraform state list
~~~

Expected resources include:

- VPC
- Two public subnets
- Internet Gateway
- Route table
- Security group
- Two EC2 instances
- S3 bucket
- S3 bucket versioning
- One unattached EBS volume

---

## Run Cost Janitor

~~~bash
cd ..
python3 -m venv .venv
source .venv/bin/activate
pip install -r janitor/requirements.txt
python janitor/janitor.py --dry-run
~~~

The Janitor writes reports to:

~~~text
janitor/reports/report.json
janitor/reports/report.md
~~~

Sample reports are included in:

~~~text
samples/report.example.json
samples/report.example.md
~~~

---

## Report Format

The JSON report includes:

- Scan timestamp
- Account ID
- Region
- Summary
- Total findings
- Estimated monthly waste
- Resource-level findings

Example finding:

~~~json
{
  "resource_id": "vol-xxxxxxxx",
  "resource_type": "ebs_volume",
  "reason": "unattached",
  "age_days": 0,
  "estimated_monthly_cost_usd": 0.8,
  "tags": {
    "Project": "NimbusKart",
    "Environment": "staging",
    "Owner": "devops"
  },
  "suggested_action": "delete",
  "safe_to_auto_delete": true
}
~~~

---

## Delete Mode

The Janitor supports delete mode:

~~~bash
python janitor/janitor.py --delete
~~~

Delete mode only deletes resources that are marked safe for auto-delete.

Resources tagged with:

~~~text
Protected=true
~~~

are skipped.

---

## GitHub Actions

The workflow file is located at:

~~~text
.github/workflows/cost-janitor.yml
~~~

The workflow runs on push and pull requests.

It performs these steps:

1. Starts LocalStack
2. Runs Terraform init
3. Runs Terraform validate
4. Applies Terraform
5. Installs Python dependencies
6. Runs the Janitor in dry-run mode
7. Uploads generated reports as artifacts
8. Fails the workflow if cost issues are found

---

## Decisions and Deviations

LocalStack was used instead of real AWS so the project can run safely without cloud billing.

S3 bucket versioning is enabled. The assignment asked for lifecycle expiration for non-current versions after 30 days, but LocalStack timed out on `GetBucketLifecycleConfiguration` while Terraform was applying the lifecycle resource. Because of that LocalStack limitation, the lifecycle rule was removed from active apply and documented here. In real AWS, I would enable the lifecycle rule.

LocalStack creates EC2 root volumes without inheriting instance tags. The Janitor reports those volumes as missing required tags. This is useful because it demonstrates tag hygiene detection.

The security group allows SSH from `0.0.0.0/0` for assignment simplicity. In production, SSH should be restricted to a trusted CIDR or replaced with AWS Systems Manager Session Manager.

---

## Cleanup

Destroy Terraform resources:

~~~bash
cd terraform
terraform destroy -auto-approve
~~~

Stop LocalStack:

~~~bash
docker stop localstack
~~~

Remove local runtime files if needed:

~~~bash
rm -rf .venv
rm -rf janitor/reports
rm -rf terraform/.terraform
rm -f terraform/terraform.tfstate terraform/terraform.tfstate.backup
~~~

---

## Final Result

The project successfully provisions local AWS-style infrastructure, runs a Python Cost Janitor, detects cost hygiene issues, and generates JSON and Markdown reports.

The sample run detected:

- One known unattached EBS volume
- Missing tag findings on LocalStack-created EC2 root volumes

This proves the Janitor can detect both cost waste and tagging governance issues.
