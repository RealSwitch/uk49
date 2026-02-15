variable "aws_region" {
  description = "AWS region"
  type        = string
  default     = "us-east-1"
}

variable "project_name" {
  description = "Project name for resource naming"
  type        = string
  default     = "uk49"
}

variable "environment" {
  description = "Environment (dev, staging, prod)"
  type        = string
  default     = "dev"
}

variable "db_name" {
  description = "Database name"
  type        = string
  default     = "uk49"
}

variable "db_username" {
  description = "Database master username"
  type        = string
  default     = "uk49admin"
  sensitive   = true
}

variable "db_password" {
  description = "Database master password (min 8 chars, alphanumeric + special)"
  type        = string
  sensitive   = true
}

variable "db_instance_class" {
  description = "RDS instance type"
  type        = string
  default     = "db.t3.micro"
}

variable "allocated_storage" {
  description = "Allocated storage in GB"
  type        = number
  default     = 20
}

variable "max_allocated_storage" {
  description = "Maximum allocated storage for autoscaling (GB)"
  type        = number
  default     = 100
}

variable "engine_version" {
  description = "PostgreSQL version"
  type        = string
  default     = "15.3"
}

variable "skip_final_snapshot" {
  description = "Skip final DB snapshot on destroy (set to false for prod)"
  type        = bool
  default     = true
}

variable "publicly_accessible" {
  description = "Make RDS publicly accessible (not recommended for prod)"
  type        = bool
  default     = false
}

variable "vpc_id" {
  description = "VPC ID (if empty, uses default VPC)"
  type        = string
  default     = ""
}

variable "allowed_cidr_blocks" {
  description = "CIDR blocks allowed to access RDS"
  type        = list(string)
  default     = ["10.0.0.0/8"]  # Private network, update for your setup
}

variable "tags" {
  description = "Common tags for all resources"
  type        = map(string)
  default = {
    Terraform = "true"
  }
}
