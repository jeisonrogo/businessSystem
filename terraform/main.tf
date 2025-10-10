# =============================================================================
# AWS Multi-Tenant Business System Infrastructure
# Optimized for cost-efficiency using AWS Free Tier and minimal services
# =============================================================================

terraform {
  required_version = ">= 1.0"

  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
    random = {
      source  = "hashicorp/random"
      version = "~> 3.4"
    }
  }

  # Uncomment and configure for remote state
  # backend "s3" {
  #   bucket = "your-terraform-state-bucket"
  #   key    = "business-system/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# =============================================================================
# PROVIDER CONFIGURATION
# =============================================================================

provider "aws" {
  region  = var.aws_region
  profile = var.aws_profile

  default_tags {
    tags = {
      Project     = var.project_name
      Environment = var.environment
      ManagedBy   = "Terraform"
      Owner       = var.owner
      CostCenter  = var.cost_center
    }
  }
}

# =============================================================================
# LOCAL VALUES
# =============================================================================

locals {
  name_prefix = "${var.project_name}-${var.environment}"

  common_tags = {
    Project     = var.project_name
    Environment = var.environment
    ManagedBy   = "Terraform"
    Owner       = var.owner
  }

  # AZ selection for cost optimization (use only 2 AZs)
  availability_zones = slice(data.aws_availability_zones.available.names, 0, 2)
}

# =============================================================================
# DATA SOURCES
# =============================================================================

data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_caller_identity" "current" {}

# =============================================================================
# RANDOM PASSWORD FOR RDS
# =============================================================================

resource "random_password" "db_password" {
  length  = 16
  special = true
}

# =============================================================================
# VPC MODULE
# =============================================================================

module "vpc" {
  source = "./modules/vpc"

  name_prefix        = local.name_prefix
  vpc_cidr          = var.vpc_cidr
  availability_zones = local.availability_zones

  # Cost optimization: Single NAT Gateway
  enable_nat_gateway     = true
  single_nat_gateway     = true
  enable_vpn_gateway     = false
  enable_dns_hostnames   = true
  enable_dns_support     = true

  tags = local.common_tags
}

# =============================================================================
# RDS MODULE
# =============================================================================

module "rds" {
  source = "./modules/rds"

  name_prefix               = local.name_prefix
  vpc_id                   = module.vpc.vpc_id
  subnet_ids               = module.vpc.private_subnet_ids
  allowed_security_group_ids = [module.app_runner.security_group_id]

  # Database configuration
  engine         = "postgres"
  engine_version = "15.7"
  instance_class = "db.t3.micro"  # Free Tier eligible

  allocated_storage     = 10
  max_allocated_storage = 100
  storage_encrypted     = true

  db_name  = var.db_name
  username = var.db_username
  password = random_password.db_password.result

  # Cost optimization
  multi_az               = false  # Disable for cost savings
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"

  # Monitoring
  monitoring_interval = 60
  enabled_cloudwatch_logs_exports = ["postgresql"]

  tags = local.common_tags
}

# =============================================================================
# APP RUNNER MODULE
# =============================================================================

module "app_runner" {
  source = "./modules/app-runner"

  name_prefix = local.name_prefix
  vpc_id      = module.vpc.vpc_id
  subnet_ids  = module.vpc.private_subnet_ids

  # Container configuration
  container_image_uri = var.backend_image_uri
  container_port     = 8000

  # Environment variables
  environment_variables = {
    DATABASE_URL = "postgresql://${var.db_username}:${random_password.db_password.result}@${module.rds.endpoint}:5432/${var.db_name}"
    AWS_REGION   = var.aws_region
    AWS_S3_BUCKET = module.s3_files.bucket_name
    ENVIRONMENT  = var.environment
    JWT_SECRET_KEY = var.jwt_secret_key
    ALLOWED_ORIGINS = "https://${var.domain_name}"
  }

  # Scaling configuration
  max_concurrency = 100
  max_size        = 10
  min_size        = 1

  # Auto scaling
  auto_scaling_enabled          = true
  auto_scaling_max_concurrency  = 100
  auto_scaling_min_size         = 1
  auto_scaling_max_size         = 10

  tags = local.common_tags
}

# =============================================================================
# S3 FRONTEND MODULE
# =============================================================================

module "s3_frontend" {
  source = "./modules/s3-frontend"

  name_prefix   = local.name_prefix
  domain_name   = var.domain_name

  # CloudFront configuration
  price_class = "PriceClass_100"  # Cost optimization

  # SSL configuration
  certificate_arn = var.ssl_certificate_arn

  tags = local.common_tags
}

# =============================================================================
# S3 FILES STORAGE
# =============================================================================

module "s3_files" {
  source = "./modules/s3-frontend"  # Reuse module but for files

  name_prefix   = "${local.name_prefix}-files"
  domain_name   = "files.${var.domain_name}"

  # Different configuration for files
  price_class = "PriceClass_100"

  # Enable versioning for files
  enable_versioning = true

  # Lifecycle rules for cost optimization
  lifecycle_rules = [
    {
      id     = "transition_to_ia"
      status = "Enabled"

      transitions = [
        {
          days          = 30
          storage_class = "STANDARD_IA"
        },
        {
          days          = 90
          storage_class = "GLACIER"
        }
      ]
    }
  ]

  tags = local.common_tags
}

# =============================================================================
# MONITORING MODULE
# =============================================================================

module "monitoring" {
  source = "./modules/monitoring"

  name_prefix = local.name_prefix

  # Resources to monitor
  app_runner_service_arn = module.app_runner.service_arn
  rds_instance_id       = module.rds.instance_id
  s3_bucket_name        = module.s3_frontend.bucket_name
  cloudfront_distribution_id = module.s3_frontend.cloudfront_distribution_id

  # Alert configuration
  alert_email = var.alert_email

  # Cost alerts
  billing_alert_threshold = var.billing_alert_threshold

  tags = local.common_tags
}

# =============================================================================
# ROUTE 53 (DNS)
# =============================================================================

data "aws_route53_zone" "main" {
  count = var.domain_name != "" ? 1 : 0
  name  = var.domain_name
}

resource "aws_route53_record" "main" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = var.domain_name
  type    = "A"

  alias {
    name                   = module.s3_frontend.cloudfront_domain_name
    zone_id                = module.s3_frontend.cloudfront_hosted_zone_id
    evaluate_target_health = false
  }
}

resource "aws_route53_record" "api" {
  count   = var.domain_name != "" ? 1 : 0
  zone_id = data.aws_route53_zone.main[0].zone_id
  name    = "api.${var.domain_name}"
  type    = "CNAME"
  ttl     = 300
  records = [module.app_runner.service_url]
}

# =============================================================================
# SECRETS MANAGER
# =============================================================================

resource "aws_secretsmanager_secret" "db_password" {
  name                    = "${local.name_prefix}-db-password"
  description            = "RDS PostgreSQL password"
  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "db_password" {
  secret_id     = aws_secretsmanager_secret.db_password.id
  secret_string = jsonencode({
    username = var.db_username
    password = random_password.db_password.result
    host     = module.rds.endpoint
    port     = 5432
    dbname   = var.db_name
  })
}