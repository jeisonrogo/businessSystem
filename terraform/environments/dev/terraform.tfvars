# =============================================================================
# DEVELOPMENT ENVIRONMENT CONFIGURATION
# Business System Multi-Tenant - DEV Environment
# =============================================================================

# =============================================================================
# GENERAL CONFIGURATION
# =============================================================================
project_name = "business-system"
environment  = "dev"
owner       = "Development Team"
cost_center = "Engineering"

# =============================================================================
# AWS CONFIGURATION
# =============================================================================
aws_region  = "us-east-1"  # Use us-east-1 for maximum Free Tier benefits
aws_profile = "personal"   # AWS CLI profile to use
vpc_cidr    = "10.0.0.0/16"

# =============================================================================
# DATABASE CONFIGURATION (Optimized for development)
# =============================================================================
db_name                    = "business_system_dev"
db_username               = "business_admin"
db_instance_class         = "db.t3.micro"  # Free Tier eligible
db_allocated_storage      = 20             # Minimum for Free Tier
db_max_allocated_storage  = 50             # Conservative limit for dev
db_backup_retention_period = 1             # Minimal backup for dev
db_multi_az               = false          # Cost optimization for dev

# =============================================================================
# APPLICATION CONFIGURATION
# =============================================================================
# Note: Update this with your actual ECR image URI after building
backend_image_uri = "public.ecr.aws/docker/library/python:3.11-slim"

# Generate a secure JWT secret key for development
# You can generate one with: openssl rand -base64 32
jwt_secret_key = "dev-jwt-secret-key-change-this-in-production-use-openssl-rand-base64-32"

# App Runner configuration - minimal for development
app_runner_cpu            = 256    # 0.25 vCPU - minimum
app_runner_memory         = 512    # 0.5 GB - minimum
app_runner_min_size       = 1      # Single instance for dev
app_runner_max_size       = 3      # Limited scaling for dev
app_runner_max_concurrency = 80    # Conservative for dev

# =============================================================================
# FRONTEND CONFIGURATION
# =============================================================================
# Leave empty for now - will use CloudFront domain
domain_name = ""

# Leave empty for now - will be created separately if needed
ssl_certificate_arn = ""

# Use most cost-effective CloudFront price class
cloudfront_price_class = "PriceClass_100"

# =============================================================================
# MONITORING AND ALERTING
# =============================================================================
# Add your email for development alerts
alert_email = "developer@yourcompany.com"

# Conservative billing alert for development
billing_alert_threshold = 25

# Disable detailed monitoring for cost savings
enable_detailed_monitoring = false

# =============================================================================
# COST OPTIMIZATION FOR DEVELOPMENT
# =============================================================================
# Enable NAT Gateway but use single gateway for cost savings
enable_nat_gateway  = true
single_nat_gateway = true

# Enable S3 cost optimization features
s3_lifecycle_rules_enabled = true
s3_intelligent_tiering    = true

# =============================================================================
# BACKUP AND RETENTION (Minimal for development)
# =============================================================================
cloudwatch_log_retention_days = 3  # Short retention for dev

# Disable deletion protection for easier development iteration
enable_deletion_protection = false

# =============================================================================
# NETWORKING (Cost optimized for development)
# =============================================================================
enable_vpn_gateway = false    # Not needed for development
enable_flow_logs   = false    # Save costs in development

# =============================================================================
# SECURITY FEATURES (Basic for development)
# =============================================================================
enable_waf                      = false  # Not needed for development
enable_shield_advanced          = false  # Expensive, not needed for dev
enable_route53_health_checks    = false  # Not critical for development

# =============================================================================
# DEVELOPMENT SPECIFIC SETTINGS
# =============================================================================
create_test_data           = true   # Create sample data for development
allow_public_rds_access    = false  # Keep secure even in development
skip_final_snapshot        = true   # Allow easy destruction in development

# =============================================================================
# ADDITIONAL TAGS FOR DEVELOPMENT
# =============================================================================
additional_tags = {
  Purpose           = "Development"
  AutoShutdown     = "true"           # Tag for potential auto-shutdown scripts
  BackupRequired   = "false"          # No critical data in development
  MonitoringLevel  = "basic"          # Basic monitoring only
  CostOptimized    = "true"           # Prioritize cost savings
  DataClassification = "non-sensitive" # Development data classification
}

# =============================================================================
# NOTES FOR DEVELOPMENT ENVIRONMENT
# =============================================================================
#
# This configuration is optimized for:
# 1. Maximum use of AWS Free Tier
# 2. Minimal costs for development work
# 3. Easy iteration and testing
# 4. Quick setup and teardown
#
# Estimated monthly cost: $15-20 (with Free Tier in first year)
# Estimated monthly cost: $30-35 (after Free Tier expires)
#
# To deploy this environment:
# 1. Review and update the variables above
# 2. Ensure you have AWS credentials configured
# 3. Run: terraform init
# 4. Run: terraform plan -var-file="environments/dev/terraform.tfvars"
# 5. Run: terraform apply -var-file="environments/dev/terraform.tfvars"
#
# Remember to:
# - Update backend_image_uri after building your container
# - Update jwt_secret_key with a secure value
# - Update alert_email with your actual email
# - Configure domain_name and ssl_certificate_arn if using custom domain
#