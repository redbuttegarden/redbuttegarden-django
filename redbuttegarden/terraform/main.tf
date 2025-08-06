provider "aws" {
  region  = "us-east-1"
  alias   = "us_east_1"
  profile = "terraform"
}

data "aws_route53_zone" "main" {
  name         = "redbuttegarden.org"
  private_zone = false
}

resource "aws_vpc" "main" {
  cidr_block = var.vpc_cidr

  tags = {
    Name = "rbg-web-${var.environment}-vpc"
  }
}

resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block = element(var.public_subnet_cidrs, count.index)
  map_public_ip_on_launch = true
  availability_zone = element(var.public_subnet_azs, count.index)

  tags = {
    Name = "rbg-web-${var.environment}-public-subnet-${count.index + 1}"
  }
}

resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)
  vpc_id = aws_vpc.main.id
  cidr_block = element(var.private_subnet_cidrs, count.index)
  availability_zone = element(var.private_subnet_azs, count.index)

  tags = {
    Name = "rbg-web-${var.environment}-private-subnet-${count.index + 1}"
  }
}

resource "aws_security_group" "main" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    cidr_blocks = [var.local_vpn_cidr]
  }

  # Allow all traffic from within the same security group
  ingress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    self      = true
  }

  egress {
    from_port = 0
    to_port   = 0
    protocol  = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_db_subnet_group" "main" {
  name       = "${var.environment}-db-subnet-group"
  subnet_ids = aws_subnet.private[*].id
}

resource "aws_acm_certificate" "env_cert" {
  provider          = aws.us_east_1
  domain_name       = "${var.environment}.redbuttegarden.org"
  validation_method = "DNS"

  tags = {
    Project     = "rbg-web-${var.environment}",
    Environment = var.environment
    Project     = "redbuttegarden"
  }
}

resource "aws_route53_record" "env_cert_validation" {
  name    = tolist(aws_acm_certificate.env_cert.domain_validation_options)[0].resource_record_name
  type    = tolist(aws_acm_certificate.env_cert.domain_validation_options)[0].resource_record_type
  zone_id = data.aws_route53_zone.main.zone_id
  records = [tolist(aws_acm_certificate.env_cert.domain_validation_options)[0].resource_record_value]
  ttl     = 60
}

resource "aws_acm_certificate_validation" "env_cert_validation" {
  provider        = aws.us_east_1
  certificate_arn = aws_acm_certificate.env_cert.arn
  validation_record_fqdns = [aws_route53_record.env_cert_validation.fqdn]
}

resource "aws_iam_role" "rds_monitoring" {
  name = "${var.environment}-rds-monitoring-role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Effect = "Allow",
        Principal = {
          Service = "monitoring.rds.amazonaws.com"
        },
        Action = "sts:AssumeRole"
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "rds_monitoring_policy" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

resource "aws_db_instance" "main" {
  identifier_prefix            = "rbg-web-${var.environment}-db-"
  allocated_storage            = 20
  engine                       = "postgres"
  engine_version               = "16.8"
  instance_class               = "db.t3.micro"
  db_subnet_group_name         = aws_db_subnet_group.main.name
  vpc_security_group_ids       = [aws_security_group.main.id]
  skip_final_snapshot          = true
  enabled_cloudwatch_logs_exports = ["postgresql"]
  monitoring_interval          = 60
  performance_insights_enabled = false
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn
  snapshot_identifier          = var.rds_snapshot_id
  storage_encrypted            = true
  lifecycle {
    ignore_changes = [snapshot_identifier]
  }
}

resource "aws_s3_bucket" "code_bucket" {
  bucket        = "rbg-code-${var.environment}"
  force_destroy = true
}

resource "aws_s3_bucket" "static_bucket" {
  bucket        = "rbg-static-${var.environment}"
  force_destroy = true
}

resource "null_resource" "copy_s3_objects" {
  provisioner "local-exec" {
    command = "aws s3 sync s3://rbg-web-static s3://${aws_s3_bucket.static_bucket.bucket} --exclude \"*/VR-Tours/*\""
  }

  triggers = {
    bucket_name = aws_s3_bucket.static_bucket.bucket
  }

  depends_on = [aws_s3_bucket.static_bucket]
}

resource "aws_s3_bucket_ownership_controls" "private_code_bucket" {
  bucket = aws_s3_bucket.code_bucket.id

  depends_on = [aws_s3_bucket.code_bucket]
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_ownership_controls" "private_static_bucket" {
  bucket = aws_s3_bucket.static_bucket.id

  depends_on = [aws_s3_bucket.static_bucket]
  rule {
    object_ownership = "BucketOwnerPreferred"
  }
}

resource "aws_s3_bucket_acl" "private_code_bucket" {
  depends_on = [aws_s3_bucket_ownership_controls.private_code_bucket]

  bucket = aws_s3_bucket.code_bucket.id
  acl    = "private"
}

resource "aws_s3_bucket_acl" "private_static_bucket" {
  depends_on = [aws_s3_bucket_ownership_controls.private_static_bucket]

  bucket = aws_s3_bucket.static_bucket.id
  acl    = "private"
}

resource "aws_cloudfront_cache_policy" "no_cache_with_csrf" {
  name = "NoCacheWithCSRF"

  default_ttl = 1
  max_ttl     = 1
  min_ttl     = 1

  parameters_in_cache_key_and_forwarded_to_origin {
    enable_accept_encoding_brotli = true
    enable_accept_encoding_gzip   = true

    cookies_config {
      cookie_behavior = "all"
    }

    headers_config {
      header_behavior = "whitelist"
      headers {
        items = [
          "Authorization",
          "Origin",
          "Referer",
          "X-Requested-With",
          "X-CSRFToken"
        ]
      }
    }

    query_strings_config {
      query_string_behavior = "all"
    }
  }

}

resource "aws_cloudfront_distribution" "cdn" {
  aliases = ["${var.environment}.redbuttegarden.org"]

  origin {
    domain_name = var.lambda_endpoint_url
    origin_id   = "code-bucket-origin"
    origin_path = "/${var.environment}"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols = ["TLSv1.2"]
    }

    custom_header {
      name  = "X-Forwarded-Host"
      value = "${var.environment}.redbuttegarden.org"
    }
  }

  origin {
    domain_name              = "${aws_s3_bucket.static_bucket.bucket}.s3.amazonaws.com"
    origin_id                = "static-bucket-origin"
    origin_access_control_id = var.cloudfront_origin_access_id
  }

  default_cache_behavior {
    target_origin_id       = "code-bucket-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods = ["GET", "HEAD"]
    cache_policy_id        = "53a64cc9-dc83-47e0-80e1-68fcd20d45f9" # Custom Zappa-Django-Cache Policy
  }

  # Do not cache the staticfiles.json file
  ordered_cache_behavior {
    path_pattern               = "/static/staticfiles.json"
    target_origin_id           = "static-bucket-origin"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods = ["GET", "HEAD"]
    cache_policy_id = "4135ea2d-6df8-44a3-9df3-4b5a84be39ad" # S3-Static-Content-NoCache Policy
    origin_request_policy_id = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" # Managed-CORS-S3Origin
    response_headers_policy_id = "60669652-455b-4ae9-85a4-c4c02393f86c" # Managed-SimpleCORS
  }

  ordered_cache_behavior {
    path_pattern               = "/static/*"
    target_origin_id           = "static-bucket-origin"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods = ["GET", "HEAD"]
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # S3-Static-Content-Cache Policy
    origin_request_policy_id = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" # Managed-CORS-S3Origin
    response_headers_policy_id = "60669652-455b-4ae9-85a4-c4c02393f86c" # Managed-SimpleCORS
  }

  ordered_cache_behavior {
    path_pattern               = "/media/*"
    target_origin_id           = "static-bucket-origin"
    viewer_protocol_policy     = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods = ["GET", "HEAD"]
    cache_policy_id = "658327ea-f89d-4fab-a63d-7e88639e58f6" # S3-Static-Content-Cache Policy
    origin_request_policy_id = "88a5eaf4-2fd4-4709-b370-b4c650ea3fcf" # Managed-CORS-S3Origin
    response_headers_policy_id = "60669652-455b-4ae9-85a4-c4c02393f86c" # Managed-SimpleCORS
  }

  ordered_cache_behavior {
    path_pattern           = "/admin/*"
    target_origin_id       = "code-bucket-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods = ["GET", "HEAD"]
    cache_policy_id        = aws_cloudfront_cache_policy.no_cache_with_csrf.id
  }

  ordered_cache_behavior {
    path_pattern           = "*/api/*"
    target_origin_id       = "code-bucket-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods = ["GET", "HEAD"]
    cache_policy_id        = aws_cloudfront_cache_policy.no_cache_with_csrf.id
  }

  ordered_cache_behavior {
    path_pattern           = "/accounts/*"
    target_origin_id       = "code-bucket-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS", "PUT", "POST", "PATCH", "DELETE"]
    cached_methods = ["GET", "HEAD"]
    cache_policy_id        = aws_cloudfront_cache_policy.no_cache_with_csrf.id
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    acm_certificate_arn      = aws_acm_certificate.env_cert.arn
    ssl_support_method       = "sni-only"
    minimum_protocol_version = "TLSv1.2_2021"
  }

  depends_on = [aws_acm_certificate_validation.env_cert_validation]

  tags = {
    Name = "rbg-web-${var.environment}",
  }
  enabled = true
}

resource "aws_s3_bucket_policy" "cloudfront_access" {
  bucket = aws_s3_bucket.static_bucket.id

  policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Sid    = "AllowCloudFrontServicePrincipalReadWrite",
        Effect = "Allow",
        Principal = {
          Service = "cloudfront.amazonaws.com"
        },
        Action = [
          "s3:GetObject",
          "s3:PutObject",
          "s3:DeleteObject"
        ],
        Resource = "arn:aws:s3:::rbg-static-${var.environment}/*",
        Condition = {
          StringEquals = {
            "AWS:SourceArn" = aws_cloudfront_distribution.cdn.arn
          }
        }
      }
    ]
  })
}

resource "aws_route53_record" "env_alias" {
  zone_id = data.aws_route53_zone.main.zone_id
  name    = "${var.environment}.redbuttegarden.org"
  type    = "A"

  alias {
    name                   = aws_cloudfront_distribution.cdn.domain_name
    zone_id                = aws_cloudfront_distribution.cdn.hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_cloudwatch_log_group" "rds_postgres_logs" {
  name              = "/aws/rds/instance/${aws_db_instance.main.id}/postgresql/rbg-web-${var.environment}"
  retention_in_days = 14
}

# Additions for NAT Gateway, Internet Gateway, and Route Tables

resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id
}

resource "aws_eip" "nat" {
  depends_on = [aws_internet_gateway.main]
}

resource "aws_nat_gateway" "main" {
  allocation_id = aws_eip.nat.id
  subnet_id     = aws_subnet.public[
  0
  ].id
  depends_on = [aws_internet_gateway.main]
}

resource "aws_route_table" "public" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.main.id
  }

  tags = {
    Name = "rbg-web-${var.environment}-public-route-table"
  }
}

resource "aws_route_table" "private" {
  vpc_id = aws_vpc.main.id

  route {
    cidr_block     = "0.0.0.0/0"
    nat_gateway_id = aws_nat_gateway.main.id
  }

  tags = {
    Name = "rbg-web-${var.environment}-private-route-table"
  }
}

resource "aws_route_table_association" "public" {
  count = length(aws_subnet.public)
  subnet_id      = aws_subnet.public[count.index].id
  route_table_id = aws_route_table.public.id
}

resource "aws_route_table_association" "private" {
  count = length(aws_subnet.private)
  subnet_id      = aws_subnet.private[count.index].id
  route_table_id = aws_route_table.private.id
}
