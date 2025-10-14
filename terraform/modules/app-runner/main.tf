# =============================================================================
# AWS APP RUNNER MODULE
# Cost-optimized serverless application deployment
# =============================================================================

# =============================================================================
# SECURITY GROUP FOR VPC CONNECTOR
# =============================================================================

resource "aws_security_group" "app_runner" {
  name_prefix = "${var.name_prefix}-app-runner-"
  description = "Security group for App Runner VPC connector"
  vpc_id      = var.vpc_id

  egress {
    description = "Allow all outbound traffic"
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-app-runner-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# VPC CONNECTOR
# =============================================================================

resource "aws_apprunner_vpc_connector" "main" {
  vpc_connector_name = "${var.name_prefix}-connector"
  subnets            = var.subnet_ids
  security_groups    = [aws_security_group.app_runner.id]

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-vpc-connector"
    }
  )
}

# =============================================================================
# IAM ROLE FOR APP RUNNER
# =============================================================================

data "aws_iam_policy_document" "app_runner_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app_runner" {
  name_prefix        = "${substr(var.name_prefix, 0, 20)}-ar-"
  assume_role_policy = data.aws_iam_policy_document.app_runner_assume_role.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "app_runner_ecr" {
  role       = aws_iam_role.app_runner.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"
}

# =============================================================================
# IAM ROLE FOR APP RUNNER INSTANCE
# =============================================================================

data "aws_iam_policy_document" "app_runner_instance_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["tasks.apprunner.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "app_runner_instance" {
  name_prefix        = "${substr(var.name_prefix, 0, 20)}-ari-"
  assume_role_policy = data.aws_iam_policy_document.app_runner_instance_assume_role.json

  tags = var.tags
}

# Policy for accessing other AWS services
data "aws_iam_policy_document" "app_runner_instance_policy" {
  statement {
    sid = "S3Access"
    actions = [
      "s3:GetObject",
      "s3:PutObject",
      "s3:DeleteObject",
      "s3:ListBucket"
    ]
    resources = ["*"]
  }

  statement {
    sid = "SecretsManagerAccess"
    actions = [
      "secretsmanager:GetSecretValue"
    ]
    resources = ["*"]
  }

  statement {
    sid = "CloudWatchLogs"
    actions = [
      "logs:CreateLogGroup",
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "app_runner_instance" {
  name_prefix = "${substr(var.name_prefix, 0, 20)}-arip-"
  role        = aws_iam_role.app_runner_instance.id
  policy      = data.aws_iam_policy_document.app_runner_instance_policy.json
}

# =============================================================================
# APP RUNNER SERVICE
# =============================================================================

resource "aws_apprunner_service" "main" {
  service_name = "${var.name_prefix}-backend"

  source_configuration {
    authentication_configuration {
      access_role_arn = aws_iam_role.app_runner.arn
    }

    image_repository {
      image_identifier      = var.container_image_uri
      image_repository_type = "ECR"

      image_configuration {
        port = tostring(var.container_port)
        start_command = "python -m uvicorn main:app --host 0.0.0.0 --port 8000"

        runtime_environment_variables = var.environment_variables
      }
    }

    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu               = "1024"  # 1 vCPU - required for FastAPI + SQLAlchemy
    memory            = "2048"  # 2 GB - required for production workload
    instance_role_arn = aws_iam_role.app_runner_instance.arn
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.main.arn
    }
  }

  health_check_configuration {
    protocol            = "HTTP"
    path                = "/health"
    interval            = 10
    timeout             = 5
    healthy_threshold   = 1
    unhealthy_threshold = 5
  }

  auto_scaling_configuration_arn = aws_apprunner_auto_scaling_configuration_version.main.arn

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-app-runner-service"
    }
  )
}

# =============================================================================
# AUTO SCALING CONFIGURATION
# =============================================================================

resource "aws_apprunner_auto_scaling_configuration_version" "main" {
  auto_scaling_configuration_name = "${var.name_prefix}-autoscaling"

  max_concurrency = var.auto_scaling_max_concurrency
  max_size        = var.auto_scaling_max_size
  min_size        = var.auto_scaling_min_size

  tags = var.tags
}
