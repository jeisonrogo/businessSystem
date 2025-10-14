# =============================================================================
# APP RUNNER MODULE OUTPUTS
# =============================================================================

output "service_arn" {
  description = "ARN of the App Runner service"
  value       = aws_apprunner_service.main.arn
}

output "service_id" {
  description = "ID of the App Runner service"
  value       = aws_apprunner_service.main.service_id
}

output "service_url" {
  description = "URL of the App Runner service"
  value       = aws_apprunner_service.main.service_url
}

output "service_status" {
  description = "Status of the App Runner service"
  value       = aws_apprunner_service.main.status
}

output "security_group_id" {
  description = "Security group ID for App Runner"
  value       = aws_security_group.app_runner.id
}

output "vpc_connector_arn" {
  description = "ARN of the VPC connector"
  value       = aws_apprunner_vpc_connector.main.arn
}

output "instance_role_arn" {
  description = "ARN of the instance role"
  value       = aws_iam_role.app_runner_instance.arn
}
