terraform {
  required_version = ">= 1.5.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.0"
    }
  }
}

provider "aws" {
  region                      = var.aws_region
  access_key                  = "test"
  secret_key                  = "test"
  skip_credentials_validation = true
  skip_metadata_api_check     = true
  skip_requesting_account_id  = true
  s3_use_path_style           = true

  endpoints {
    ec2 = "http://localhost:4566"
    s3  = "http://localhost:4566"
  }
}

locals {
  common_tags = {
    Project     = var.project
    Environment = var.environment
    Owner       = var.owner
    ManagedBy   = "terraform"
  }
}

module "network" {
  source = "./modules/network"

  vpc_cidr     = var.vpc_cidr
  subnet_cidrs = var.public_subnet_cidrs
  azs          = var.azs
  common_tags  = local.common_tags
}

resource "aws_security_group" "web" {
  name        = "${var.project}-${var.environment}-web-sg"
  description = "Web security group for NimbusKart staging"
  vpc_id      = module.network.vpc_id

  ingress {
    description = "HTTP from anywhere"
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "HTTPS from anywhere"
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH from configurable CIDR"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = [var.ssh_cidr]
  }

  egress {
    description = "Allow all outbound"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(local.common_tags, {
    Name = "${var.project}-${var.environment}-web-sg"
  })
}

resource "aws_instance" "web" {
  count = 2

  ami                         = var.ami_id
  instance_type               = var.instance_type
  subnet_id                   = module.network.public_subnet_ids[count.index]
  vpc_security_group_ids      = [aws_security_group.web.id]
  associate_public_ip_address = true

  tags = merge(local.common_tags, {
    Name = "${var.project}-${var.environment}-web-${count.index + 1}"
    Tier = "web"
  })
}

resource "aws_s3_bucket" "logs" {
  bucket = var.logs_bucket_name

  tags = merge(local.common_tags, {
    Name = var.logs_bucket_name
  })
}

resource "aws_s3_bucket_versioning" "logs" {
  bucket = aws_s3_bucket.logs.id

  versioning_configuration {
    status = "Enabled"
  }
}

resource "aws_ebs_volume" "orphan" {
  availability_zone = var.azs[0]
  size              = 10
  type              = "gp3"

  tags = merge(local.common_tags, {
    Name = "${var.project}-${var.environment}-known-orphan-volume"
  })
}
