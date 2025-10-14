# =============================================================================
# TERRAFORM OUTPUTS
# Business System Multi-Tenant - AWS Infrastructure
# =============================================================================

# =============================================================================
# VPC OUTPUTS
# =============================================================================

output "vpc_id" {
  description = "ID of the VPC"
  value       = module.vpc.vpc_id
}

output "private_subnet_ids" {
  description = "IDs of private subnets"
  value       = module.vpc.private_subnet_ids
}

output "public_subnet_ids" {
  description = "IDs of public subnets"
  value       = module.vpc.public_subnet_ids
}

# =============================================================================
# RDS OUTPUTS
# =============================================================================

output "rds_endpoint" {
  description = "RDS instance endpoint"
  value       = module.rds.endpoint
  sensitive   = true
}

output "rds_address" {
  description = "RDS instance address"
  value       = module.rds.address
}

# =============================================================================
# APP RUNNER OUTPUTS
# =============================================================================

output "app_runner_service_url" {
  description = "App Runner service URL"
  value       = module.app_runner.service_url
}

output "app_runner_service_arn" {
  description = "App Runner service ARN"
  value       = module.app_runner.service_arn
}

output "app_runner_service_id" {
  description = "App Runner service ID"
  value       = module.app_runner.service_id
}

output "backend_url" {
  description = "Backend API URL"
  value       = "https://${module.app_runner.service_url}"
}

# =============================================================================
# S3 FRONTEND OUTPUTS
# =============================================================================

output "frontend_bucket_name" {
  description = "S3 bucket name for frontend"
  value       = module.s3_frontend.bucket_name
}

output "frontend_cloudfront_domain" {
  description = "CloudFront distribution domain for frontend"
  value       = module.s3_frontend.cloudfront_domain_name
}

output "frontend_cloudfront_url" {
  description = "Frontend URL via CloudFront"
  value       = "https://${module.s3_frontend.cloudfront_domain_name}"
}

# =============================================================================
# S3 FILES OUTPUTS
# =============================================================================

output "files_bucket_name" {
  description = "S3 bucket name for file storage"
  value       = module.s3_files.bucket_name
}

output "files_cloudfront_domain" {
  description = "CloudFront distribution domain for files"
  value       = module.s3_files.cloudfront_domain_name
}

# =============================================================================
# SECRETS MANAGER OUTPUTS
# =============================================================================

output "db_secret_arn" {
  description = "ARN of the database credentials secret"
  value       = aws_secretsmanager_secret.db_password.arn
  sensitive   = true
}

# =============================================================================
# GENERAL OUTPUTS
# =============================================================================

output "aws_region" {
  description = "AWS region where resources are deployed"
  value       = var.aws_region
}

output "environment" {
  description = "Environment name"
  value       = var.environment
}

output "project_name" {
  description = "Project name"
  value       = var.project_name
}

# =============================================================================
# DEPLOYMENT INFO
# =============================================================================

output "deployment_info" {
  description = "Summary of deployment endpoints"
  value = {
    frontend_url = "https://${module.s3_frontend.cloudfront_domain_name}"
    backend_url  = "https://${module.app_runner.service_url}"
    environment  = var.environment
    region       = var.aws_region
  }
}
