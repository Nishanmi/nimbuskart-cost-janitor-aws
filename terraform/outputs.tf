output "vpc_id" {
  description = "VPC ID"
  value       = module.network.vpc_id
}

output "public_subnet_ids" {
  description = "Public subnet IDs"
  value       = module.network.public_subnet_ids
}

output "logs_bucket_name" {
  description = "S3 logs bucket name"
  value       = aws_s3_bucket.logs.bucket
}

output "web_instance_ids" {
  description = "Web EC2 instance IDs"
  value       = aws_instance.web[*].id
}

output "known_orphan_volume_id" {
  description = "Known unattached EBS volume for janitor testing"
  value       = aws_ebs_volume.orphan.id
}
