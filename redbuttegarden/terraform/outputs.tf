output "vpc_id" {
  value = aws_vpc.main.id
}

output "public_subnet_ids" {
  value = aws_subnet.public[*].id
}

output "private_subnet_ids" {
  value = aws_subnet.private[*].id
}

output "security_group_id" {
  value = aws_security_group.main.id
}

output "db_instance_endpoint" {
  value = aws_db_instance.main.endpoint
}

output "cloudfront_distribution_id" {
  value = aws_cloudfront_distribution.cdn.id
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.cdn.domain_name
}

output "code_bucket_name" {
  value = aws_s3_bucket.code_bucket.bucket
}

output "static_bucket_name" {
  value = aws_s3_bucket.static_bucket.bucket
}

output "iam_role_arn" {
  value = aws_iam_role.zappa_execution.arn
}
