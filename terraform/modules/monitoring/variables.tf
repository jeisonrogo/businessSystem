# =============================================================================
# MONITORING MODULE VARIABLES
# =============================================================================

variable "name_prefix" {
  description = "Prefix for resource names"
  type        = string
}

variable "app_runner_service_arn" {
  description = "ARN of the App Runner service to monitor"
  type        = string
}

variable "rds_instance_id" {
  description = "ID of the RDS instance to monitor"
  type        = string
}

variable "s3_bucket_name" {
  description = "Name of the S3 bucket to monitor"
  type        = string
}

variable "cloudfront_distribution_id" {
  description = "ID of the CloudFront distribution to monitor"
  type        = string
}

variable "alert_email" {
  description = "Email address for alerts"
  type        = string
  default     = ""
}

variable "billing_alert_threshold" {
  description = "Billing alert threshold in USD"
  type        = number
  default     = 50
}

variable "tags" {
  description = "Tags to apply to resources"
  type        = map(string)
  default     = {}
}
