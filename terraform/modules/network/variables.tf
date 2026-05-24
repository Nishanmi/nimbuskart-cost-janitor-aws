variable "vpc_cidr" {
  description = "VPC CIDR"
  type        = string
}

variable "subnet_cidrs" {
  description = "Subnet CIDRs"
  type        = list(string)
}

variable "azs" {
  description = "Availability zones"
  type        = list(string)
}

variable "common_tags" {
  description = "Common resource tags"
  type        = map(string)
}
