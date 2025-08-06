variable "environment" {
  description = "Environment name (dev, staging)"
  type        = string
}

variable "vpc_cidr" {
  description = "CIDR block for the VPC"
  type        = string
}

variable "local_vpn_cidr" {
  description = "CIDR block for the local VPN"
  type        = string
}

variable "public_subnet_cidrs" {
  description = "CIDR blocks for public subnets"
  type = list(string)
}

variable "private_subnet_cidrs" {
  description = "CIDR blocks for private subnets"
  type = list(string)
}

variable "public_subnet_azs" {
  type = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "private_subnet_azs" {
  type = list(string)
  default = ["us-east-1a", "us-east-1b"]
}

variable "lambda_endpoint_url" {
  description = "URL of the Lambda function endpoint"
  type        = string
  default     = null
}

variable "rds_snapshot_id" {
  description = "Snapshot ID for the RDS instance"
  type        = string
}

variable "cloudfront_origin_access_id" {
  description = "Cloudfront origin access ID"
  type        = string
  default = "update-me-after-zappa-deployment"
}