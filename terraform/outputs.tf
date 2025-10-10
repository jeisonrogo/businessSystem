# =============================================================================
# TERRAFORM OUTPUTS
# Business System Multi-Tenant Deployment
# =============================================================================

# =============================================================================
# NETWORKING OUTPUTS
# =============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "vpc_cidr_block" {
  description = "CIDR block of the VPC"
  value       = module.vpc.vpc_cidr_block
}

output "public_subnet_ids" {
  description = "List of public subnet IDs"
  value       = module.vpc.public_subnet_ids
}

output "private_subnet_ids" {
  description = "List of private subnet IDs"
  value       = module.vpc.private_subnet_ids
}

output "internet_gateway_id" {
  description = "ID of the Internet Gateway"
  value       = module.vpc.internet_gateway_id
}

output "nat_gateway_ids" {
  description = "List of NAT Gateway IDs"
  value       = module.vpc.nat_gateway_ids
}

# =============================================================================
# DATABASE OUTPUTS
# =============================================================================

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "rds_instance_id" {
  description = "RDS instance ID"
  value       = module.rds.instance_id
}

output "rds_port" {
  description = "RDS instance port"
  value       = module.rds.port
}

output "rds_database_name" {
  description = "RDS database name"
  value       = module.rds.database_name
}

output "rds_security_group_id" {
  description = "Security group ID for RDS"
  value       = module.rds.security_group_id
}

# =============================================================================
# APPLICATION OUTPUTS
# =============================================================================

output "app_runner_service_arn" {
  description = "App Runner service ARN"
  value       = module.app_runner.service_arn
}

output "app_runner_service_url" {
  description = "App Runner service URL"
  value       = module.app_runner.service_url
}

output "app_runner_service_id" {
  description = "App Runner service ID"
  value       = module.app_runner.service_id
}

output "app_runner_security_group_id" {
  description = "Security group ID for App Runner"
  value       = module.app_runner.security_group_id
}

# =============================================================================
# FRONTEND OUTPUTS
# =============================================================================

output "s3_frontend_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = module.s3_frontend.bucket_name
}

output "s3_frontend_bucket_website_endpoint" {
  description = "S3 bucket website endpoint"
  value       = module.s3_frontend.bucket_website_endpoint
}

output "cloudfront_distribution_id" {
  description = "CloudFront distribution ID"
  value       = module.s3_frontend.cloudfront_distribution_id
}

output "cloudfront_distribution_domain_name" {
  description = "CloudFront distribution domain name"
  value       = module.s3_frontend.cloudfront_domain_name
}

output "cloudfront_hosted_zone_id" {
  description = "CloudFront hosted zone ID"
  value       = module.s3_frontend.cloudfront_hosted_zone_id
}

# =============================================================================
# FILE STORAGE OUTPUTS
# =============================================================================

output "s3_files_bucket_name" {
  description = "S3 bucket name for file storage"
  value       = module.s3_files.bucket_name
}

output "s3_files_bucket_arn" {
  description = "S3 bucket ARN for file storage"
  value       = module.s3_files.bucket_arn
}

# =============================================================================
# MONITORING OUTPUTS
# =============================================================================

output "cloudwatch_log_group_names" {
  description = "CloudWatch log group names"
  value       = module.monitoring.log_group_names
}

output "sns_topic_arn" {
  description = "SNS topic ARN for alerts"
  value       = module.monitoring.sns_topic_arn
}

output "cloudwatch_dashboard_url" {
  description = "CloudWatch dashboard URL"
  value       = module.monitoring.dashboard_url
}

# =============================================================================
# DNS OUTPUTS
# =============================================================================

output "route53_zone_id" {
  description = "Route 53 hosted zone ID"
  value       = var.domain_name != "" ? data.aws_route53_zone.main[0].zone_id : null
}

output "domain_name" {
  description = "Domain name for the application"
  value       = var.domain_name
}

output "api_domain_name" {
  description = "API domain name"
  value       = var.domain_name != "" ? "api.${var.domain_name}" : null
}

# =============================================================================
# SECURITY OUTPUTS
# =============================================================================

output "secrets_manager_secret_arn" {
  description = "Secrets Manager secret ARN for database credentials"
  value       = aws_secretsmanager_secret.db_password.arn
  sensitive   = true
}

output "secrets_manager_secret_name" {
  description = "Secrets Manager secret name for database credentials"
  value       = aws_secretsmanager_secret.db_password.name
}

# =============================================================================
# COST OUTPUTS
# =============================================================================

output "estimated_monthly_cost" {
  description = "Estimated monthly cost breakdown (informational)"
  value = {
    rds_instance       = "$13.70 (Free Tier: $0)"
    app_runner        = "$8-15 (based on usage)"
    s3_storage        = "$0.50 (Free Tier: $0)"
    cloudfront        = "$1.00 (Free Tier: $0)"
    nat_gateway       = "$3.50"
    data_transfer     = "$2.00"
    cloudwatch_logs   = "$1.00"
    route53           = "$0.50"
    total_without_free_tier = "$30-35"
    total_with_free_tier    = "$17-20 (first 12 months)"
  }
}

# =============================================================================
# CONNECTION INFORMATION
# =============================================================================

output "database_connection_info" {
  description = "Database connection information"
  value = {
    host     = module.rds.endpoint
    port     = module.rds.port
    database = module.rds.database_name
    username = var.db_username
    # Password is stored in Secrets Manager
    secrets_manager_secret = aws_secretsmanager_secret.db_password.name
  }
  sensitive = true
}

output "application_urls" {
  description = "Application URLs"
  value = {
    frontend_cloudfront = module.s3_frontend.cloudfront_domain_name
    frontend_custom     = var.domain_name != "" ? "https://${var.domain_name}" : null
    backend_app_runner  = "https://${module.app_runner.service_url}"
    backend_custom      = var.domain_name != "" ? "https://api.${var.domain_name}" : null
  }
}

# =============================================================================
# DEPLOYMENT INFORMATION
# =============================================================================

output "deployment_info" {
  description = "Deployment information and next steps"
  value = {
    terraform_workspace = terraform.workspace
    aws_region         = var.aws_region
    environment        = var.environment
    project_name       = var.project_name

    next_steps = [
      "1. Deploy backend container to ECR",
      "2. Update App Runner service with new image",
      "3. Build and upload frontend to S3",
      "4. Run database migrations",
      "5. Configure DNS records (if using custom domain)",
      "6. Set up monitoring alerts",
      "7. Test application end-to-end"
    ]

    useful_commands = {
      get_db_password     = "aws secretsmanager get-secret-value --secret-id ${aws_secretsmanager_secret.db_password.name} --query SecretString --output text"
      view_app_runner_logs = "aws logs tail /aws/apprunner/${module.app_runner.service_name}/application --follow"
      sync_frontend       = "aws s3 sync ./frontend/build s3://${module.s3_frontend.bucket_name}"
      invalidate_cloudfront = "aws cloudfront create-invalidation --distribution-id ${module.s3_frontend.cloudfront_distribution_id} --paths '/*'"
    }
  }
}

# =============================================================================
# RESOURCE ARNS (for CI/CD and automation)
# =============================================================================

output "resource_arns" {
  description = "ARNs of key resources for automation"
  value = {
    app_runner_service = module.app_runner.service_arn
    rds_instance      = module.rds.instance_arn
    s3_frontend_bucket = module.s3_frontend.bucket_arn
    s3_files_bucket   = module.s3_files.bucket_arn
    cloudfront_distribution = module.s3_frontend.cloudfront_arn
    secrets_manager_secret = aws_secretsmanager_secret.db_password.arn
  }
}

# =============================================================================
# TAGS OUTPUT
# =============================================================================

output "common_tags" {
  description = "Common tags applied to all resources"
  value       = local.common_tags
}