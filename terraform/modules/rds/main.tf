# =============================================================================
# RDS POSTGRESQL MODULE
# Cost-optimized database for development
# =============================================================================

# =============================================================================
# SECURITY GROUP
# =============================================================================

resource "aws_security_group" "rds" {
  name_prefix = "${var.name_prefix}-rds-"
  description = "Security group for RDS PostgreSQL"
  vpc_id      = var.vpc_id

  ingress {
    description     = "PostgreSQL from App Runner"
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = var.allowed_security_group_ids
  }

  # Conditional ingress rule for public access from specific IPs
  dynamic "ingress" {
    for_each = var.allow_public_access && length(var.allowed_cidr_blocks) > 0 ? [1] : []
    content {
      description = "PostgreSQL from allowed CIDR blocks"
      from_port   = 5432
      to_port     = 5432
      protocol    = "tcp"
      cidr_blocks = var.allowed_cidr_blocks
    }
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
      Name = "${var.name_prefix}-rds-sg"
    }
  )

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# SUBNET GROUP
# =============================================================================

resource "aws_db_subnet_group" "main" {
  name_prefix = "${var.name_prefix}-"
  subnet_ids  = var.subnet_ids

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-rds-subnet-group"
    }
  )
}

# =============================================================================
# PARAMETER GROUP
# =============================================================================

resource "aws_db_parameter_group" "main" {
  name_prefix = "${var.name_prefix}-"
  family      = "postgres15"
  description = "Parameter group for ${var.name_prefix}"

  # Optimization for small instances
  parameter {
    name         = "shared_buffers"
    value        = "16384"  # 128MB for t3.micro
    apply_method = "pending-reboot"
  }

  parameter {
    name         = "max_connections"
    value        = "100"
    apply_method = "pending-reboot"
  }

  parameter {
    name         = "work_mem"
    value        = "4096"  # 4MB
    apply_method = "immediate"
  }

  tags = var.tags

  lifecycle {
    create_before_destroy = true
  }
}

# =============================================================================
# MONITORING ROLE
# =============================================================================

data "aws_iam_policy_document" "rds_monitoring_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]

    principals {
      type        = "Service"
      identifiers = ["monitoring.rds.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "rds_monitoring" {
  name_prefix        = "${substr(var.name_prefix, 0, 20)}-rdsm-"
  assume_role_policy = data.aws_iam_policy_document.rds_monitoring_assume_role.json

  tags = var.tags
}

resource "aws_iam_role_policy_attachment" "rds_monitoring" {
  role       = aws_iam_role.rds_monitoring.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole"
}

# =============================================================================
# RDS INSTANCE
# =============================================================================

resource "aws_db_instance" "main" {
  identifier     = "${var.name_prefix}-db"
  engine         = var.engine
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage     = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type          = "gp3"
  storage_encrypted     = var.storage_encrypted

  db_name  = var.db_name
  username = var.username
  password = var.password

  db_subnet_group_name   = aws_db_subnet_group.main.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  parameter_group_name   = aws_db_parameter_group.main.name

  multi_az               = var.multi_az
  publicly_accessible    = var.allow_public_access
  backup_retention_period = var.backup_retention_period
  backup_window          = var.backup_window
  maintenance_window     = var.maintenance_window

  enabled_cloudwatch_logs_exports = var.enabled_cloudwatch_logs_exports
  monitoring_interval             = var.monitoring_interval
  monitoring_role_arn            = aws_iam_role.rds_monitoring.arn

  auto_minor_version_upgrade = true
  deletion_protection        = false
  skip_final_snapshot        = true

  tags = merge(
    var.tags,
    {
      Name = "${var.name_prefix}-database"
    }
  )
}
