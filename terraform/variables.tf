variable "aws_region" {
  description = "AWS region used by LocalStack"
  type        = string
  default     = "us-east-1"
}

variable "project" {
  description = "Project tag"
  type        = string
  default     = "NimbusKart"
}

variable "environment" {
  description = "Environment tag"
  type        = string
  default     = "staging"
}

variable "owner" {
  description = "Owner tag"
  type        = string
  default     = "devops"
}

variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
  default     = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  description = "Public subnet CIDRs"
  type        = list(string)
  default     = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "azs" {
  description = "Availability zones"
  type        = list(string)
  default     = ["us-east-1a", "us-east-1b"]
}

variable "ssh_cidr" {
  description = "CIDR allowed for SSH. Assignment default is 0.0.0.0/0, but this is unsafe for production."
  type        = string
  default     = "0.0.0.0/0"
}

variable "ami_id" {
  description = "Dummy AMI ID for LocalStack EC2"
  type        = string
  default     = "ami-12345678"
}

variable "instance_type" {
  description = "EC2 instance type"
  type        = string
  default     = "t3.micro"
}

variable "logs_bucket_name" {
  description = "S3 bucket for app logs"
  type        = string
  default     = "nimbuskart-staging-app-logs"
}
