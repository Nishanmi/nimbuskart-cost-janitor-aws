# Submission — DevOps Engineer Assignment

**Candidate name:** Nishant Mishra  
**Email:** nishant.mishra1784@gmail.com  
**Date submitted:** 2026-05-24  
**Hours spent (approximate):** 5 hours  

## Deliverables checklist
- [x] Part A: Terraform code under /terraform applies cleanly on LocalStack
- [x] Part A: `terraform validate` and `terraform fmt -check` both pass
- [x] Part B: Janitor script runs in --dry-run mode and produces report.json
- [ ] Part B: GitHub Actions workflow runs green on a fresh PR
- [x] Part B: --delete mode respects Protected=true tag
- [x] Part C: DESIGN.md is present and within 2 pages
- [x] Walkthrough video link below is accessible (unlisted is fine)

## Walkthrough video
Link (Loom / YouTube unlisted / Google Drive): https://www.loom.com/share/b2d220dcd04a4d05b68f1938ce8ad63f  
Length: max 5 minutes

## Sample report
Path to a sample report.json produced by your script: `samples/report.example.json`

## Known limitations
- S3 lifecycle configuration was documented but not kept active because LocalStack timed out while reading lifecycle configuration.
- The project is AWS-focused right now; GCP and Azure are described in DESIGN.md as future provider adapters.
- Cost estimates use static pricing constants instead of live cloud pricing APIs.
- LocalStack-created EC2 root volumes may not inherit all instance tags, so they can appear as missing-tag findings.

## AI usage disclosure
I used ChatGPT to help debug Terraform/LocalStack issues, structure documentation, and improve the walkthrough explanation. One thing AI suggested badly was keeping the S3 lifecycle resource active even though LocalStack kept timing out; I noticed this during terraform apply and documented it as a LocalStack limitation instead. I manually reviewed the final Terraform outputs, Janitor report, and design decisions so I could explain them in the walkthrough video.
