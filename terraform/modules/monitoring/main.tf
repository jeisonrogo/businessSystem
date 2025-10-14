# =============================================================================
# MONITORING MODULE
# CloudWatch alarms and SNS topics for monitoring
# =============================================================================

# =============================================================================
# SNS TOPIC FOR ALERTS
# =============================================================================

resource "aws_sns_topic" "alerts" {
  name_prefix = "${var.name_prefix}-alerts-"

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-alerts"
    }
  )
}

resource "aws_sns_topic_subscription" "email" {
  count     = var.alert_email != "" ? 1 : 0
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# =============================================================================
# CLOUDWATCH LOG GROUPS
# =============================================================================

resource "aws_cloudwatch_log_group" "app_runner" {
  name_prefix       = "/aws/apprunner/${var.name_prefix}-"
  retention_in_days = 3  # Cost optimization for dev

  tags = var.tags
}

resource "aws_cloudwatch_log_group" "rds" {
  name_prefix       = "/aws/rds/${var.name_prefix}-"
  retention_in_days = 3  # Cost optimization for dev

  tags = var.tags
}

# =============================================================================
# CLOUDWATCH ALARMS - RDS
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "rds_cpu" {
  alarm_name          = "${var.name_prefix}-rds-cpu-high"
  alarm_description   = "RDS CPU utilization is too high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "rds_storage" {
  alarm_name          = "${var.name_prefix}-rds-storage-low"
  alarm_description   = "RDS free storage space is low"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = 1
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 2000000000  # 2 GB

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "rds_connections" {
  alarm_name          = "${var.name_prefix}-rds-connections-high"
  alarm_description   = "RDS database connections are high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80

  dimensions = {
    DBInstanceIdentifier = var.rds_instance_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# =============================================================================
# CLOUDWATCH ALARMS - CLOUDFRONT
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "cloudfront_error_rate" {
  alarm_name          = "${var.name_prefix}-cloudfront-error-rate"
  alarm_description   = "CloudFront 5xx error rate is high"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "5xxErrorRate"
  namespace           = "AWS/CloudFront"
  period              = 300
  statistic           = "Average"
  threshold           = 5

  dimensions = {
    DistributionId = var.cloudfront_distribution_id
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# =============================================================================
# BILLING ALARM
# =============================================================================

resource "aws_cloudwatch_metric_alarm" "billing" {
  count               = var.alert_email != "" ? 1 : 0
  alarm_name          = "${var.name_prefix}-billing-threshold"
  alarm_description   = "AWS billing threshold exceeded"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 1
  metric_name         = "EstimatedCharges"
  namespace           = "AWS/Billing"
  period              = 21600  # 6 hours
  statistic           = "Maximum"
  threshold           = var.billing_alert_threshold

  dimensions = {
    Currency = "USD"
  }

  alarm_actions = [aws_sns_topic.alerts.arn]

  tags = var.tags
}

# =============================================================================
# CLOUDWATCH DASHBOARD
# =============================================================================

resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "${var.name_prefix}-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "CPUUtilization", { stat = "Average", label = "RDS CPU" }],
            ["AWS/RDS", "DatabaseConnections", { stat = "Average", label = "DB Connections" }]
          ]
          period = 300
          stat   = "Average"
          region = data.aws_region.current.name
          title  = "RDS Metrics"
        }
      },
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/CloudFront", "Requests", { stat = "Sum", label = "Requests" }],
            ["AWS/CloudFront", "5xxErrorRate", { stat = "Average", label = "5xx Errors" }]
          ]
          period = 300
          stat   = "Average"
          region = "us-east-1"  # CloudFront metrics are in us-east-1
          title  = "CloudFront Metrics"
        }
      }
    ]
  })
}

# =============================================================================
# DATA SOURCES
# =============================================================================

data "aws_region" "current" {}
