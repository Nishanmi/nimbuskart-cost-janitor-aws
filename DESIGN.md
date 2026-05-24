# Design Note

## 1. Multi-cloud reality

To support GCP next quarter and Azure later, I would keep the Janitor core cloud-agnostic and move cloud-specific logic into provider adapters.

The module boundaries would be:

~~~text
janitor/
├── core/
│   ├── models.py          # common Finding, Resource, Report objects
│   ├── rules.py           # shared rules like missing tags, protected resources
│   ├── reporter.py        # JSON and Markdown report generation
│   └── policy.py          # delete safety checks
├── providers/
│   ├── aws/
│   │   ├── inventory.py   # EC2, EBS, EIP discovery using boto3
│   │   └── actions.py     # delete/tag actions for AWS
│   ├── gcp/
│   │   ├── inventory.py   # Compute disks, VMs, static IPs using GCP SDK
│   │   └── actions.py
│   └── azure/
│       ├── inventory.py   # Managed disks, VMs, public IPs using Azure SDK
│       └── actions.py
└── cli.py
~~~

The core should only understand normalized resources such as `volume`, `instance`, `public_ip`, tags/labels, age, state, and estimated cost. AWS, GCP, and Azure adapters would convert provider-specific resources into this common format. This way, adding GCP would mostly mean adding a new provider adapter instead of rewriting reporting, safety checks, CLI flags, or deletion logic.

## 2. Permissions

In `--dry-run` mode, the Janitor only needs read-only permissions to list resources, inspect tags, and estimate waste. It should not have permission to delete, detach, stop, or modify anything.

In `--delete` mode, the Janitor needs the same read permissions plus tightly scoped delete permissions only for resources it is allowed to clean up, such as unattached EBS volumes and unused Elastic IPs. I would separate these into two IAM roles: one read-only role for scheduled reporting and one delete role that is used only after approval.

Minimal AWS read-only IAM policy for dry-run mode:

~~~json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "Ec2InventoryReadOnly",
      "Effect": "Allow",
      "Action": [
        "ec2:DescribeInstances",
        "ec2:DescribeVolumes",
        "ec2:DescribeAddresses",
        "ec2:DescribeTags",
        "ec2:DescribeRegions"
      ],
      "Resource": "*"
    },
    {
      "Sid": "S3InventoryReadOnly",
      "Effect": "Allow",
      "Action": [
        "s3:ListAllMyBuckets",
        "s3:GetBucketTagging",
        "s3:GetBucketVersioning",
        "s3:GetLifecycleConfiguration"
      ],
      "Resource": "*"
    },
    {
      "Sid": "StsIdentityReadOnly",
      "Effect": "Allow",
      "Action": [
        "sts:GetCallerIdentity"
      ],
      "Resource": "*"
    }
  ]
}
~~~

For delete mode, I would add only actions such as `ec2:DeleteVolume`, `ec2:ReleaseAddress`, and possibly `ec2:CreateTags`, with conditions requiring approved tags like `JanitorApproved=true` and denying deletion when `Protected=true`.

## 3. Safety net

One failure mode is deleting an unattached EBS volume that is actually a recent database backup or a volume temporarily detached during maintenance. A naïve script may see it as unused and delete it immediately. The guardrail would be a minimum age threshold, for example only delete unattached volumes older than 7 or 14 days, skip anything tagged `Protected=true`, and require `JanitorApproved=true` before delete mode can remove it.

Another failure mode is releasing an Elastic IP that is temporarily unused during a blue/green deployment or failover. If that IP is allowlisted by customers or partners, releasing it could cause an outage even if it is currently unattached. The guardrail would be to never auto-release EIPs unless they are older than a threshold, have no DNS reference, have no owner exemption tag, and appear in at least two consecutive janitor scans.

I would also keep delete mode separate from dry-run mode, publish a report first, and require manual approval for production accounts.

## 4. Observability

I would publish these metrics to CloudWatch in AWS, and later to the equivalent monitoring system for GCP/Azure or a central Prometheus/Grafana setup.

| Metric | Source | Alert threshold |
|---|---|---|
| `janitor_findings_total` | Count of findings in each report | Alert if greater than 0 in production for 2 consecutive runs |
| `janitor_estimated_waste_usd` | Sum of estimated monthly waste from report summary | Alert if above 50 USD in staging or above 200 USD in production |
| `janitor_delete_actions_total` | Count of successful delete actions in delete mode | Alert if greater than 10 in one run |
| `janitor_scan_failures_total` | CLI exit code, exceptions, or failed workflow runs | Alert on any failure |
| `janitor_protected_skips_total` | Count of resources skipped because `Protected=true` | Alert if it suddenly increases by more than 50% week over week |

These metrics help the FinOps team see whether waste is decreasing, whether the Janitor is running successfully, and whether delete mode is behaving safely.

## 5. What I did not build

I did not build real multi-cloud support, real AWS deployment, approval workflows, historical trend storage, or full cost calculation using live pricing APIs. I kept the project focused on the assignment requirements: LocalStack infrastructure, AWS-style resource discovery, safe dry-run reporting, basic delete support, and CI automation. I also did not keep the S3 lifecycle rule active in Terraform because LocalStack timed out while reading the lifecycle configuration; in real AWS I would enable non-current version expiration after 30 days.
