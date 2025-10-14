# =============================================================================
# MONITORING MODULE OUTPUTS
# =============================================================================

output "sns_topic_arn" {
  description = "ARN of the SNS topic for alerts"
  value       = aws_sns_topic.alerts.arn
}

output "dashboard_name" {
  description = "Name of the CloudWatch dashboard"
  value       = aws_cloudwatch_dashboard.main.dashboard_name
}

output "app_runner_log_group_name" {
  description = "Name of the App Runner log group"
  value       = aws_cloudwatch_log_group.app_runner.name
}

output "rds_log_group_name" {
  description = "Name of the RDS log group"
  value       = aws_cloudwatch_log_group.rds.name
}
