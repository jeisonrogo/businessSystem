# =============================================================================
# ECS FARGATE MODULE - ULTRA ECONÓMICO
# Costo estimado: ~$5-7/mes con Fargate SPOT
# =============================================================================

# =============================================================================
# ECS CLUSTER
# =============================================================================

resource "aws_ecs_cluster" "main" {
  name = "${var.name_prefix}-cluster"

  setting {
    name  = "containerInsights"
    value = "disabled"  # Deshabilitado para ahorrar costos
  }

  tags = var.tags
}

# =============================================================================
# CLOUDWATCH LOG GROUP
# =============================================================================

resource "aws_cloudwatch_log_group" "ecs" {
  name              = "/ecs/${var.name_prefix}"
  retention_in_days = 3  # Solo 3 días para minimizar costos

  tags = var.tags
}

# =============================================================================
# ECS TASK EXECUTION ROLE
# =============================================================================

data "aws_iam_policy_document" "ecs_task_execution_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_execution_role" {
  name_prefix        = "${substr(var.name_prefix, 0, 20)}-exec-"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_execution_role.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "ecs_task_execution_role_policy" {
  role       = aws_iam_role.ecs_task_execution_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy"
}

# =============================================================================
# ECS TASK ROLE (para acceder a S3, Secrets Manager, etc)
# =============================================================================

data "aws_iam_policy_document" "ecs_task_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["ecs-tasks.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "ecs_task_role" {
  name_prefix        = "${substr(var.name_prefix, 0, 20)}-task-"
  assume_role_policy = data.aws_iam_policy_document.ecs_task_role.json

  tags = var.tags
}

data "aws_iam_policy_document" "ecs_task_policy" {
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
      "logs:CreateLogStream",
      "logs:PutLogEvents"
    ]
    resources = ["${aws_cloudwatch_log_group.ecs.arn}:*"]
  }
}

resource "aws_iam_role_policy" "ecs_task_policy" {
  name_prefix = "${substr(var.name_prefix, 0, 20)}-task-pol-"
  role        = aws_iam_role.ecs_task_role.id
  policy      = data.aws_iam_policy_document.ecs_task_policy.json
}

# =============================================================================
# SECURITY GROUP FOR ECS TASKS
# =============================================================================

resource "aws_security_group" "ecs_tasks" {
  name_prefix = "${var.name_prefix}-ecs-tasks-"
  description = "Security group for ECS tasks"
  vpc_id      = var.vpc_id

  ingress {
    description     = "Allow traffic from ALB"
    from_port       = var.container_port
    to_port         = var.container_port
    protocol        = "tcp"
    security_groups = [var.alb_security_group_id]
  }

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
      Name = "${var.name_prefix}-ecs-tasks-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# ECS TASK DEFINITION
# =============================================================================

resource "aws_ecs_task_definition" "main" {
  family                   = "${var.name_prefix}-backend"
  network_mode             = "awsvpc"
  requires_compatibilities = ["FARGATE"]
  cpu                      = "256"   # 0.25 vCPU - mínimo de Fargate
  memory                   = "512"   # 512 MB - mínimo de Fargate
  execution_role_arn       = aws_iam_role.ecs_task_execution_role.arn
  task_role_arn            = aws_iam_role.ecs_task_role.arn

  container_definitions = jsonencode([
    {
      name      = "backend"
      image     = var.container_image_uri
      essential = true

      portMappings = [
        {
          containerPort = var.container_port
          protocol      = "tcp"
        }
      ]

      environment = [
        for key, value in var.environment_variables : {
          name  = key
          value = value
        }
      ]

      logConfiguration = {
        logDriver = "awslogs"
        options = {
          "awslogs-group"         = aws_cloudwatch_log_group.ecs.name
          "awslogs-region"        = var.aws_region
          "awslogs-stream-prefix" = "ecs"
        }
      }

      healthCheck = {
        command     = ["CMD-SHELL", "curl -f http://localhost:${var.container_port}/health || exit 1"]
        interval    = 30
        timeout     = 5
        retries     = 3
        startPeriod = 60
      }
    }
  ])

  tags = var.tags
}

# =============================================================================
# ECS SERVICE
# =============================================================================

resource "aws_ecs_service" "main" {
  name            = "${var.name_prefix}-backend"
  cluster         = aws_ecs_cluster.main.id
  task_definition = aws_ecs_task_definition.main.arn
  desired_count   = 1  # Solo 1 tarea para minimizar costos

  # Usar Fargate SPOT para ahorrar hasta 70%
  capacity_provider_strategy {
    capacity_provider = "FARGATE_SPOT"
    weight            = 100
    base              = 0
  }

  network_configuration {
    subnets          = var.private_subnet_ids
    security_groups  = [aws_security_group.ecs_tasks.id]
    assign_public_ip = false
  }

  load_balancer {
    target_group_arn = var.target_group_arn
    container_name   = "backend"
    container_port   = var.container_port
  }

  # Esperar a que el ALB esté listo
  depends_on = [aws_iam_role_policy.ecs_task_policy]

  tags = var.tags
}
