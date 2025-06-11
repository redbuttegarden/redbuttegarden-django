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
}

resource "aws_subnet" "public" {
  count = length(var.public_subnet_cidrs)
  vpc_id                  = aws_vpc.main.id
  cidr_block = element(var.public_subnet_cidrs, count.index)
  map_public_ip_on_launch = true
}

resource "aws_subnet" "private" {
  count = length(var.private_subnet_cidrs)
  vpc_id = aws_vpc.main.id
  cidr_block = element(var.private_subnet_cidrs, count.index)
  availability_zone = element(var.private_subnet_azs, count.index)
}

resource "aws_security_group" "main" {
  vpc_id = aws_vpc.main.id

  ingress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
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
  allocated_storage            = 20
  engine                       = "postgres"
  engine_version               = "16.8"
  instance_class               = "db.t4g.micro"
  db_name                      = "${var.environment}_db"
  username                     = var.db_username
  password                     = var.db_password
  db_subnet_group_name         = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.main.id]
  skip_final_snapshot          = true
  enabled_cloudwatch_logs_exports = ["postgresql"]
  monitoring_interval          = 60
  performance_insights_enabled = false
  monitoring_role_arn          = aws_iam_role.rds_monitoring.arn
}

resource "aws_s3_bucket" "code_bucket" {
  bucket        = "rbg-code-${var.environment}"
  force_destroy = true
}

resource "aws_s3_bucket" "static_bucket" {
  bucket        = "rbg-static-${var.environment}"
  force_destroy = true
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

resource "aws_cloudfront_distribution" "cdn" {
  origin {
    domain_name = "${aws_s3_bucket.code_bucket.bucket}.s3.amazonaws.com"
    origin_id   = "code-bucket-origin"
    origin_path = "/${var.environment}"
  }

  origin {
    domain_name = "${aws_s3_bucket.static_bucket.bucket}.s3.amazonaws.com"
    origin_id   = "static-bucket-origin"
  }

  default_cache_behavior {
    target_origin_id       = "code-bucket-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods = ["GET", "HEAD"]
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  ordered_cache_behavior {
    path_pattern           = "/static/*"
    target_origin_id       = "static-bucket-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods = ["GET", "HEAD"]
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
  }

  ordered_cache_behavior {
    path_pattern           = "/media/*"
    target_origin_id       = "static-bucket-origin"
    viewer_protocol_policy = "redirect-to-https"
    allowed_methods = ["GET", "HEAD", "OPTIONS"]
    cached_methods = ["GET", "HEAD"]
    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }
    min_ttl     = 0
    default_ttl = 3600
    max_ttl     = 86400
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
    Environment = var.environment
    Project     = "redbuttegarden"
  }
  enabled = true
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

resource "aws_iam_role" "zappa_execution" {
  name = "${var.environment}_zappa_execution_role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17",
    Statement = [
      {
        Action = "sts:AssumeRole",
        Effect = "Allow",
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "zappa_logs" {
  role       = aws_iam_role.zappa_execution.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

resource "aws_cloudwatch_log_group" "rds_postgres_logs" {
  name              = "/aws/rds/instance/${aws_db_instance.main.id}/postgresql"
  retention_in_days = 14
}
