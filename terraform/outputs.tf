output "db_endpoint" {
  description = "RDS endpoint (host:port)"
  value       = aws_db_instance.postgres.endpoint
}

output "db_host" {
  description = "RDS hostname"
  value       = aws_db_instance.postgres.address
}

output "db_port" {
  description = "RDS port"
  value       = aws_db_instance.postgres.port
}

output "db_name" {
  description = "Database name"
  value       = aws_db_instance.postgres.db_name
}

output "db_username" {
  description = "Database master username"
  value       = aws_db_instance.postgres.username
  sensitive   = true
}

output "db_connection_string" {
  description = "PostgreSQL connection string for SQLAlchemy"
  value       = "postgresql+psycopg2://${aws_db_instance.postgres.username}:<PASSWORD>@${aws_db_instance.postgres.address}:${aws_db_instance.postgres.port}/${aws_db_instance.postgres.db_name}"
  sensitive   = true
}

output "db_identifier" {
  description = "RDS instance identifier"
  value       = aws_db_instance.postgres.id
}

output "security_group_id" {
  description = "RDS security group ID"
  value       = aws_security_group.rds.id
}

output "db_subnet_group_name" {
  description = "RDS subnet group name"
  value       = aws_db_subnet_group.rds.name
}

output "db_arn" {
  description = "RDS instance ARN"
  value       = aws_db_instance.postgres.arn
}
