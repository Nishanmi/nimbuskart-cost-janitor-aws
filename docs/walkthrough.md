# Walkthrough Video

Loom link: https://www.loom.com/share/b2d220dcd04a4d05b68f1938ce8ad63f

## Transcript Summary

In the walkthrough, I start a fresh LocalStack container, apply the Terraform stack live, run the Python Cost Janitor in dry-run mode, and review one unattached EBS volume finding from the generated report.

I also point out one design decision I am proud of: separating dry-run and delete mode with safety checks like Protected=true and safe_to_auto_delete.

One thing I would change is refactoring the current AWS-focused implementation into a core engine with provider adapters for AWS, GCP, and Azure.
