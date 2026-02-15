data "aws_availability_zones" "available" {
  state = "available"
}

data "aws_vpc" "default" {
  count   = var.vpc_id == "" ? 1 : 0
  default = true
}

data "aws_subnets" "default" {
  count = var.vpc_id == "" ? 1 : 0
  filter {
    name   = "vpc-id"
    values = [data.aws_vpc.default[0].id]
  }
}

locals {
  vpc_id           = var.vpc_id != "" ? var.vpc_id : data.aws_vpc.default[0].id
  db_identifier    = "${var.project_name}-db-${var.environment}"
  sg_name          = "${var.project_name}-rds-sg-${var.environment}"
}

# Security Group for RDS
resource "aws_security_group" "rds" {
  name_prefix = local.sg_name
  description = "Security group for UK49 RDS PostgreSQL"
  vpc_id      = local.vpc_id

  tags = merge(
    var.tags,
    {
      Name = local.sg_name
    }
  )
}

# Ingress: PostgreSQL from CIDR blocks
resource "aws_vpc_security_group_ingress_rule" "postgres_internal" {
  security_group_id = aws_security_group.rds.id
  description       = "PostgreSQL from internal networks"
  from_port         = 5432
  to_port           = 5432
  ip_protocol       = "tcp"
  cidr_ipv4         = var.allowed_cidr_blocks[0]

  tags = var.tags
}

# Egress: Allow all outbound (default AWS behavior)
resource "aws_vpc_security_group_egress_rule" "all" {
  security_group_id = aws_security_group.rds.id
  description       = "Allow all outbound traffic"
  from_port         = -1
  to_port           = -1
  ip_protocol       = "-1"
  cidr_ipv4         = "0.0.0.0/0"

  tags = var.tags
}

# DB Subnet Group (required for RDS in VPC)
resource "aws_db_subnet_group" "rds" {
  name_prefix        = "${var.project_name}-"
  description        = "Subnet group for UK49 RDS"
  subnet_ids         = data.aws_subnets.default[0].ids
  skip_final_snapshot = true

  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-db-subnet-${var.environment}"
    }
  )

  depends_on = [data.aws_subnets.default]
}

# RDS PostgreSQL Instance
resource "aws_db_instance" "postgres" {
  identifier            = local.db_identifier
  allocated_storage    = var.allocated_storage
  max_allocated_storage = var.max_allocated_storage
  storage_type         = "gp3"
  engine              = "postgres"
  engine_version      = var.engine_version
  instance_class      = var.db_instance_class
  
  db_name  = var.db_name
  username = var.db_username
  password = var.db_password
  
  db_subnet_group_name   = aws_db_subnet_group.rds.name
  vpc_security_group_ids = [aws_security_group.rds.id]
  
  publicly_accessible       = var.publicly_accessible
  skip_final_snapshot       = var.skip_final_snapshot
  final_snapshot_identifier = var.skip_final_snapshot ? null : "${local.db_identifier}-final-snapshot-${formatdate("YYYY-MM-DD-hhmmss", timestamp())}"
  
  # Backup configuration
  backup_retention_period = 7
  backup_window          = "03:00-04:00"
  maintenance_window     = "sun:04:00-sun:05:00"
  
  # Performance and monitoring
  enabled_cloudwatch_logs_exports = ["postgresql"]
  performance_insights_enabled     = var.db_instance_class != "db.t3.micro" ? true : false
  
  # Encryption (default: true)
  storage_encrypted = true
  
  multi_az = var.environment == "prod" ? true : false
  
  tags = merge(
    var.tags,
    {
      Name = "${var.project_name}-db-${var.environment}"
    }
  )

  depends_on = [
    aws_security_group.rds,
    aws_db_subnet_group.rds
  ]
}

# (Optional) CloudWatch Alarms
resource "aws_cloudwatch_metric_alarm" "db_cpu" {
  count               = var.environment == "prod" ? 1 : 0
  alarm_name          = "${local.db_identifier}-cpu-utilization"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "CPUUtilization"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "75"
  alarm_description   = "Alert when RDS CPU exceeds 75%"
  alarm_actions       = []  # Add SNS topic ARN if needed

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = var.tags
}

resource "aws_cloudwatch_metric_alarm" "db_storage" {
  count               = var.environment == "prod" ? 1 : 0
  alarm_name          = "${local.db_identifier}-free-space"
  comparison_operator = "LessThanThreshold"
  evaluation_periods  = "2"
  metric_name         = "FreeStorageSpace"
  namespace           = "AWS/RDS"
  period              = "300"
  statistic           = "Average"
  threshold           = "2147483648"  # 2GB
  alarm_description   = "Alert when RDS free storage is below 2GB"
  alarm_actions       = []  # Add SNS topic ARN if needed

  dimensions = {
    DBInstanceIdentifier = aws_db_instance.postgres.id
  }

  tags = var.tags
}
