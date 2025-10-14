# =============================================================================
# TERRAFORM VARIABLES
# Business System Multi-Tenant Deployment
# =============================================================================

# =============================================================================
# GENERAL CONFIGURATION
# =============================================================================

variable "project_name" {
  description = "Name of the project"
  type        = string
  default     = "business-system"

  validation {
    condition     = can(regex("^[a-z0-9-]+$", var.project_name))
    error_message = "Project name must contain only lowercase letters, numbers, and hyphens."
  }
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
  default     = "dev"

  validation {
    condition     = contains(["dev", "staging", "prod"], var.environment)
    error_message = "Environment must be one of: dev, staging, prod."
  }
}

variable "owner" {
  description = "Owner of the resources"
  type        = string
  default     = "DevOps Team"
}

variable "cost_center" {
  description = "Cost center for billing"
  type        = string
  default     = "Engineering"
}

# =============================================================================
# AWS CONFIGURATION
# =============================================================================

variable "aws_region" {
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"

  validation {
    condition = can(regex("^[a-z0-9-]+$", var.aws_region))
    error_message = "AWS region must be a valid region identifier."
  }
}

variable "aws_profile" {
  description = "AWS profile to use for authentication"
  type        = string
  default     = "personal"

  validation {
    condition     = can(regex("^[a-zA-Z0-9_-]+$", var.aws_profile))
    error_message = "AWS profile must contain only letters, numbers, underscores, and hyphens."
  }
}

variable "vpc_cidr" {
  description = "CIDR block for VPC"
  type        = string
  default     = "10.0.0.0/16"

  validation {
    condition = can(cidrhost(var.vpc_cidr, 0))
    error_message = "VPC CIDR must be a valid IPv4 CIDR block."
  }
}

# =============================================================================
# DATABASE CONFIGURATION
# =============================================================================

variable "db_name" {
  description = "Name of the database"
  type        = string
  default     = "business_system"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_name))
    error_message = "Database name must start with a letter and contain only letters, numbers, and underscores."
  }
}

variable "db_username" {
  description = "Username for the database"
  type        = string
  default     = "business_admin"

  validation {
    condition     = can(regex("^[a-zA-Z][a-zA-Z0-9_]*$", var.db_username))
    error_message = "Database username must start with a letter and contain only letters, numbers, and underscores."
  }
}

variable "db_instance_class" {
  description = "RDS instance class"
  type        = string
  default     = "db.t3.micro"

  validation {
    condition = contains([
      "db.t3.micro", "db.t3.small", "db.t3.medium",
      "db.t4g.micro", "db.t4g.small", "db.t4g.medium"
    ], var.db_instance_class)
    error_message = "Database instance class must be a valid RDS instance type."
  }
}

variable "db_allocated_storage" {
  description = "Allocated storage for RDS instance (GB)"
  type        = number
  default     = 20

  validation {
    condition     = var.db_allocated_storage >= 20 && var.db_allocated_storage <= 1000
    error_message = "Allocated storage must be between 20 and 1000 GB."
  }
}

variable "db_max_allocated_storage" {
  description = "Maximum allocated storage for RDS auto scaling (GB)"
  type        = number
  default     = 100

  validation {
    condition     = var.db_max_allocated_storage >= var.db_allocated_storage
    error_message = "Maximum allocated storage must be greater than or equal to allocated storage."
  }
}

variable "db_backup_retention_period" {
  description = "Backup retention period in days"
  type        = number
  default     = 7

  validation {
    condition     = var.db_backup_retention_period >= 0 && var.db_backup_retention_period <= 35
    error_message = "Backup retention period must be between 0 and 35 days."
  }
}

variable "db_multi_az" {
  description = "Enable Multi-AZ for RDS (increases cost)"
  type        = bool
  default     = false
}

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================

variable "backend_image_uri" {
  description = "Container image URI for backend application"
  type        = string
  default     = "public.ecr.aws/docker/library/python:3.11-slim"

  validation {
    condition     = can(regex("^[a-zA-Z0-9][a-zA-Z0-9._/-]*:[a-zA-Z0-9._-]+$", var.backend_image_uri))
    error_message = "Backend image URI must be a valid container image reference."
  }
}

variable "jwt_secret_key" {
  description = "JWT secret key for authentication"
  type        = string
  sensitive   = true

  validation {
    condition     = length(var.jwt_secret_key) >= 32
    error_message = "JWT secret key must be at least 32 characters long."
  }
}

variable "app_runner_cpu" {
  description = "CPU units for App Runner (256, 512, 1024, 2048, 4096)"
  type        = number
  default     = 256

  validation {
    condition = contains([256, 512, 1024, 2048, 4096], var.app_runner_cpu)
    error_message = "App Runner CPU must be one of: 256, 512, 1024, 2048, 4096."
  }
}

variable "app_runner_memory" {
  description = "Memory for App Runner (512, 1024, 2048, 3072, 4096, 6144, 8192, 10240, 12288)"
  type        = number
  default     = 512

  validation {
    condition = contains([512, 1024, 2048, 3072, 4096, 6144, 8192, 10240, 12288], var.app_runner_memory)
    error_message = "App Runner memory must be a valid memory configuration."
  }
}

variable "app_runner_min_size" {
  description = "Minimum number of App Runner instances"
  type        = number
  default     = 1

  validation {
    condition     = var.app_runner_min_size >= 1 && var.app_runner_min_size <= 25
    error_message = "App Runner minimum size must be between 1 and 25."
  }
}

variable "app_runner_max_size" {
  description = "Maximum number of App Runner instances"
  type        = number
  default     = 10

  validation {
    condition     = var.app_runner_max_size >= 1 && var.app_runner_max_size <= 25
    error_message = "App Runner maximum size must be between 1 and 25."
  }
}

variable "app_runner_max_concurrency" {
  description = "Maximum concurrent requests per App Runner instance"
  type        = number
  default     = 100

  validation {
    condition     = var.app_runner_max_concurrency >= 1 && var.app_runner_max_concurrency <= 200
    error_message = "App Runner max concurrency must be between 1 and 200."
  }
}

# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================

variable "domain_name" {
  description = "Domain name for the application (e.g., example.com)"
  type        = string
  default     = ""

  validation {
    condition = var.domain_name == "" || can(regex("^[a-zA-Z0-9][a-zA-Z0-9.-]*[a-zA-Z0-9]$", var.domain_name))
    error_message = "Domain name must be a valid domain or empty string."
  }
}

variable "ssl_certificate_arn" {
  description = "ARN of SSL certificate in ACM (us-east-1 for CloudFront)"
  type        = string
  default     = ""
}

variable "cloudfront_price_class" {
  description = "CloudFront price class (PriceClass_All, PriceClass_200, PriceClass_100)"
  type        = string
  default     = "PriceClass_100"

  validation {
    condition = contains(["PriceClass_All", "PriceClass_200", "PriceClass_100"], var.cloudfront_price_class)
    error_message = "CloudFront price class must be one of: PriceClass_All, PriceClass_200, PriceClass_100."
  }
}

# =============================================================================
# MONITORING AND ALERTING
# =============================================================================

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""

  validation {
    condition = var.alert_email == "" || can(regex("^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\\.[a-zA-Z]{2,}$", var.alert_email))
    error_message = "Alert email must be a valid email address or empty string."
  }
}

variable "billing_alert_threshold" {
  description = "Billing alert threshold in USD"
  type        = number
  default     = 50

  validation {
    condition     = var.billing_alert_threshold > 0
    error_message = "Billing alert threshold must be greater than 0."
  }
}

variable "enable_detailed_monitoring" {
  description = "Enable detailed CloudWatch monitoring (additional cost)"
  type        = bool
  default     = false
}

# =============================================================================
# COST OPTIMIZATION
# =============================================================================

variable "enable_nat_gateway" {
  description = "Enable NAT Gateway for private subnets (cost optimization option)"
  type        = bool
  default     = true
}

variable "single_nat_gateway" {
  description = "Use single NAT Gateway instead of one per AZ (cost optimization)"
  type        = bool
  default     = true
}

variable "s3_lifecycle_rules_enabled" {
  description = "Enable S3 lifecycle rules for cost optimization"
  type        = bool
  default     = true
}

variable "s3_intelligent_tiering" {
  description = "Enable S3 Intelligent Tiering for automatic cost optimization"
  type        = bool
  default     = true
}

# =============================================================================
# BACKUP AND RETENTION
# =============================================================================

variable "cloudwatch_log_retention_days" {
  description = "CloudWatch logs retention period in days"
  type        = number
  default     = 14

  validation {
    condition = contains([1, 3, 5, 7, 14, 30, 60, 90, 120, 150, 180, 365, 400, 545, 731, 1827, 3653], var.cloudwatch_log_retention_days)
    error_message = "CloudWatch log retention days must be a valid retention period."
  }
}

variable "enable_deletion_protection" {
  description = "Enable deletion protection for critical resources"
  type        = bool
  default     = false
}

# =============================================================================
# NETWORKING
# =============================================================================

variable "enable_vpn_gateway" {
  description = "Enable VPN Gateway (additional cost)"
  type        = bool
  default     = false
}

variable "enable_flow_logs" {
  description = "Enable VPC Flow Logs (additional cost for storage)"
  type        = bool
  default     = false
}

# =============================================================================
# TAGS
# =============================================================================

variable "additional_tags" {
  description = "Additional tags to apply to all resources"
  type        = map(string)
  default     = {}
}

# =============================================================================
# FEATURE FLAGS
# =============================================================================

variable "enable_waf" {
  description = "Enable AWS WAF for CloudFront (additional cost)"
  type        = bool
  default     = false
}

variable "enable_shield_advanced" {
  description = "Enable AWS Shield Advanced (significant additional cost)"
  type        = bool
  default     = false
}

variable "enable_route53_health_checks" {
  description = "Enable Route 53 health checks (additional cost)"
  type        = bool
  default     = false
}

# =============================================================================
# DEVELOPMENT/TESTING
# =============================================================================

variable "create_test_data" {
  description = "Create test data and sample configurations"
  type        = bool
  default     = false
}

variable "allow_public_rds_access" {
  description = "Allow public access to RDS (NOT recommended for production)"
  type        = bool
  default     = false
}

variable "allowed_cidr_blocks" {
  description = "List of CIDR blocks allowed to access RDS (only used if allow_public_rds_access is true)"
  type        = list(string)
  default     = []

  validation {
    condition = alltrue([
      for cidr in var.allowed_cidr_blocks : can(cidrhost(cidr, 0))
    ])
    error_message = "All CIDR blocks must be valid IPv4 CIDR notation."
  }
}

variable "skip_final_snapshot" {
  description = "Skip final snapshot when destroying RDS (for development only)"
  type        = bool
  default     = false
}