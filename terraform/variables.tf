variable "aws_region" {
  default = "us-east-1"
}

variable "project" {
  default = "NimbusKart"
}

variable "environment" {
  default = "staging"
}

variable "owner" {
  default = "devops"
}

variable "ssh_cidr" {
  default = "0.0.0.0/0"
}

variable "vpc_cidr" {
  default = "10.20.0.0/16"
}

variable "public_subnet_cidrs" {
  default = ["10.20.1.0/24", "10.20.2.0/24"]
}

variable "azs" {
  default = ["us-east-1a", "us-east-1b"]
}
