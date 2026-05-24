#!/usr/bin/env python3
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import boto3
from botocore.config import Config

from constants import EBS_GP3_GB_MONTH_USD, UNUSED_EIP_MONTH_USD, STOPPED_INSTANCE_MONTH_USD

REQUIRED_TAGS = ["Project", "Environment", "Owner"]


def aws_client(service, region, endpoint_url):
    return boto3.client(
        service,
        region_name=region,
        endpoint_url=endpoint_url,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID", "test"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY", "test"),
        config=Config(retries={"max_attempts": 3, "mode": "standard"}),
    )


def tags_to_dict(tags):
    return {tag.get("Key"): tag.get("Value") for tag in tags or []}


def missing_required_tags(tag_dict):
    return [tag for tag in REQUIRED_TAGS if not tag_dict.get(tag)]


def is_protected(tag_dict):
    return str(tag_dict.get("Protected", "")).lower() == "true"


def make_finding(resource_id, resource_type, reason, age_days, cost, tags, action, safe):
    return {
        "resource_id": resource_id,
        "resource_type": resource_type,
        "reason": reason,
        "age_days": age_days,
        "estimated_monthly_cost_usd": round(float(cost), 2),
        "tags": {tag: tags.get(tag) for tag in REQUIRED_TAGS},
        "suggested_action": action,
        "safe_to_auto_delete": safe,
    }


def find_unattached_volumes(ec2):
    findings = []
    response = ec2.describe_volumes(Filters=[{"Name": "status", "Values": ["available"]}])

    for volume in response.get("Volumes", []):
        tags = tags_to_dict(volume.get("Tags", []))
        size = volume.get("Size", 0)
        cost = size * EBS_GP3_GB_MONTH_USD

        findings.append(
            make_finding(
                volume["VolumeId"],
                "ebs_volume",
                "unattached",
                0,
                cost,
                tags,
                "delete",
                not is_protected(tags),
            )
        )

    return findings


def find_stopped_instances(ec2, stopped_days):
    findings = []
    response = ec2.describe_instances(
        Filters=[{"Name": "instance-state-name", "Values": ["stopped"]}]
    )

    for reservation in response.get("Reservations", []):
        for instance in reservation.get("Instances", []):
            tags = tags_to_dict(instance.get("Tags", []))

            findings.append(
                make_finding(
                    instance["InstanceId"],
                    "ec2_instance",
                    f"stopped_more_than_{stopped_days}_days",
                    stopped_days,
                    STOPPED_INSTANCE_MONTH_USD,
                    tags,
                    "review_or_terminate",
                    False,
                )
            )

    return findings


def find_unused_eips(ec2):
    findings = []
    response = ec2.describe_addresses()

    for address in response.get("Addresses", []):
        if not address.get("AssociationId"):
            tags = tags_to_dict(address.get("Tags", []))
            resource_id = address.get("AllocationId") or address.get("PublicIp")

            findings.append(
                make_finding(
                    resource_id,
                    "elastic_ip",
                    "not_associated",
                    0,
                    UNUSED_EIP_MONTH_USD,
                    tags,
                    "release",
                    not is_protected(tags),
                )
            )

    return findings


def find_missing_tags(ec2):
    findings = []

    for volume in ec2.describe_volumes().get("Volumes", []):
        tags = tags_to_dict(volume.get("Tags", []))
        missing = missing_required_tags(tags)

        if missing:
            findings.append(
                make_finding(
                    volume["VolumeId"],
                    "ebs_volume",
                    "missing_tags:" + ",".join(missing),
                    0,
                    0,
                    tags,
                    "tag_resource",
                    False,
                )
            )

    for reservation in ec2.describe_instances().get("Reservations", []):
        for instance in reservation.get("Instances", []):
            tags = tags_to_dict(instance.get("Tags", []))
            missing = missing_required_tags(tags)

            if missing:
                findings.append(
                    make_finding(
                        instance["InstanceId"],
                        "ec2_instance",
                        "missing_tags:" + ",".join(missing),
                        0,
                        0,
                        tags,
                        "tag_resource",
                        False,
                    )
                )

    for address in ec2.describe_addresses().get("Addresses", []):
        tags = tags_to_dict(address.get("Tags", []))
        missing = missing_required_tags(tags)

        if missing:
            resource_id = address.get("AllocationId") or address.get("PublicIp")
            findings.append(
                make_finding(
                    resource_id,
                    "elastic_ip",
                    "missing_tags:" + ",".join(missing),
                    0,
                    0,
                    tags,
                    "tag_resource",
                    False,
                )
            )

    return findings


def delete_findings(ec2, findings):
    deleted = []
    skipped = []

    for item in findings:
        if not item["safe_to_auto_delete"]:
            skipped.append(item["resource_id"])
            continue

        try:
            if item["resource_type"] == "ebs_volume" and item["suggested_action"] == "delete":
                ec2.delete_volume(VolumeId=item["resource_id"])
                deleted.append(item["resource_id"])

            elif item["resource_type"] == "elastic_ip" and item["suggested_action"] == "release":
                if str(item["resource_id"]).startswith("eipalloc-"):
                    ec2.release_address(AllocationId=item["resource_id"])
                else:
                    ec2.release_address(PublicIp=item["resource_id"])
                deleted.append(item["resource_id"])

            else:
                skipped.append(item["resource_id"])

        except Exception:
            skipped.append(item["resource_id"])

    return deleted, skipped


def write_reports(report, output_dir):
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    json_path = output_path / "report.json"
    md_path = output_path / "report.md"

    json_path.write_text(json.dumps(report, indent=2))

    lines = [
        "# Cost Janitor Report",
        "",
        f"- Scan timestamp: `{report['scan_timestamp']}`",
        f"- Account ID: `{report['account_id']}`",
        f"- Region: `{report['region']}`",
        f"- Total findings: `{report['summary']['total_orphans']}`",
        f"- Estimated monthly waste: `${report['summary']['estimated_monthly_waste_usd']}`",
        "",
        "## Findings",
        "",
    ]

    if not report["findings"]:
        lines.append("No orphaned resources found.")
    else:
        for item in report["findings"]:
            lines.extend(
                [
                    f"### {item['resource_type']} - {item['resource_id']}",
                    f"- Reason: {item['reason']}",
                    f"- Suggested action: {item['suggested_action']}",
                    f"- Estimated monthly cost: ${item['estimated_monthly_cost_usd']}",
                    f"- Safe to auto-delete: {item['safe_to_auto_delete']}",
                    "",
                ]
            )

    md_path.write_text("\n".join(lines))
    return json_path, md_path


def main():
    parser = argparse.ArgumentParser(description="NimbusKart Cost Janitor")
    parser.add_argument("--region", default=os.getenv("AWS_DEFAULT_REGION", "us-east-1"))
    parser.add_argument("--endpoint-url", default=os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566"))
    parser.add_argument("--stopped-days", type=int, default=14)
    parser.add_argument("--output-dir", default="reports")
    parser.add_argument("--dry-run", action="store_true", default=True)
    parser.add_argument("--delete", action="store_true")

    args = parser.parse_args()

    ec2 = aws_client("ec2", args.region, args.endpoint_url)

    findings = []
    findings.extend(find_unattached_volumes(ec2))
    findings.extend(find_stopped_instances(ec2, args.stopped_days))
    findings.extend(find_unused_eips(ec2))
    findings.extend(find_missing_tags(ec2))

    total_cost = sum(item["estimated_monthly_cost_usd"] for item in findings)

    report = {
        "scan_timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "account_id": "000000000000",
        "region": args.region,
        "summary": {
            "total_orphans": len(findings),
            "estimated_monthly_waste_usd": round(total_cost, 2),
        },
        "findings": findings,
    }

    if args.delete:
        deleted, skipped = delete_findings(ec2, findings)
        report["delete_summary"] = {
            "deleted": deleted,
            "skipped": skipped,
        }

    json_path, md_path = write_reports(report, args.output_dir)

    print(f"Wrote {json_path}")
    print(f"Wrote {md_path}")
    print(f"Total findings: {len(findings)}")

    if findings and not args.delete:
        sys.exit(2)

    sys.exit(0)


if __name__ == "__main__":
    main()
