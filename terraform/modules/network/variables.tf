variable "project" {}
variable "environment" {}
variable "owner" {}
variable "vpc_cidr" {}
variable "public_subnet_cidrs" {
  type = list(string)
}
variable "azs" {
  type = list(string)
}
