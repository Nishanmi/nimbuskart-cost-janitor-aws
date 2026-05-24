# Cost Janitor Report

- Scan timestamp: `2026-05-24T10:08:57Z`
- Account ID: `000000000000`
- Region: `us-east-1`
- Total findings: `3`
- Estimated monthly waste: `$0.8`

## Findings

### ebs_volume - vol-ef7ed310
- Reason: unattached
- Suggested action: delete
- Estimated monthly cost: $0.8
- Safe to auto-delete: True

### ebs_volume - vol-251bbe65
- Reason: missing_tags:Project,Environment,Owner
- Suggested action: tag_resource
- Estimated monthly cost: $0.0
- Safe to auto-delete: False

### ebs_volume - vol-a8b04150
- Reason: missing_tags:Project,Environment,Owner
- Suggested action: tag_resource
- Estimated monthly cost: $0.0
- Safe to auto-delete: False
