# Terraform - AWS RDS PostgreSQL Deployment

This directory contains Terraform configuration to deploy PostgreSQL on AWS RDS for the UK49 ETL pipeline.

## Files

- `provider.tf` – AWS provider configuration
- `variables.tf` – Input variables (region, instance size, credentials, etc.)
- `main.tf` – RDS instance, security group, subnet group, CloudWatch alarms
- `outputs.tf` – Outputs (endpoint, connection string, identifiers)
- `terraform.tfvars.example` – Example values (rename & customize)

## Prerequisites

1. **AWS Account** with appropriate IAM permissions (EC2, RDS, VPC, CloudWatch)
2. **Terraform** >= 1.0 installed
3. **AWS CLI** configured with credentials:
   ```bash
   aws configure
   ```

## Quick Start

### 1. Copy and configure variables
```bash
cp terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:
- Set a **strong password** for `db_password` (20+ chars, mix of letters, numbers, special chars)
- Update `aws_region` if needed (default: `us-east-1`)
- Adjust `db_instance_class` (default: `db.t3.micro` for dev, use `db.t3.small+` for prod)
- Update `allowed_cidr_blocks` to match your VPC/bastion security groups

### 2. Initialize Terraform
```bash
terraform init
```

This downloads the AWS provider and initializes the Terraform state.

### 3. Review the plan
```bash
terraform plan -out=tfplan
```

Review the resources that will be created. Look for:
- RDS instance (`aws_db_instance.postgres`)
- Security group (`aws_security_group.rds`)
- DB subnet group (`aws_db_subnet_group.rds`)

### 4. Apply the configuration
```bash
terraform apply tfplan
```

This creates the RDS instance. It typically takes **5-10 minutes**.

### 5. Retrieve connection details
```bash
terraform output
terraform output db_connection_string
```

Example output:
```
db_endpoint = "uk49-db-dev.abc123def.us-east-1.rds.amazonaws.com:5432"
db_connection_string = "postgresql+psycopg2://uk49admin:<PASSWORD>@uk49-db-dev.abc123def.us-east-1.rds.amazonaws.com:5432/uk49"
```

## Environment Variables for Airflow/FastAPI

Update your `.env` or Docker environment with:

```bash
DATABASE_URL=postgresql+psycopg2://<username>:<password>@<endpoint>/<db_name>
```

Example:
```bash
DATABASE_URL=postgresql+psycopg2://uk49admin:YourSecurePassword@uk49-db-dev.abc123def.us-east-1.rds.amazonaws.com:5432/uk49
```

## Customization

### Change Instance Size
Edit `terraform.tfvars`:
```hcl
db_instance_class = "db.t3.small"  # Upgrade from micro
```

Then:
```bash
terraform plan -out=tfplan
terraform apply tfplan
```

### Enable Multi-AZ (High Availability)
The configuration auto-enables Multi-AZ for `environment = "prod"`. For dev, set:
```hcl
environment = "prod"
```

### Increase Storage
```hcl
allocated_storage      = 50  # increase from 20
max_allocated_storage  = 200 # auto-scale limit
```

### Update Network Access
Edit `allowed_cidr_blocks` to add your application security group:
```hcl
allowed_cidr_blocks = [
  "10.0.1.0/24",    # Airflow subnet
  "10.0.2.0/24",    # API subnet
]
```

## State Management

Terraform stores state in `terraform.tfstate` (local). For production:

1. **Use S3 backend** to store state remotely:

Create a new file `backend.tf`:
```hcl
terraform {
  backend "s3" {
    bucket         = "my-terraform-state-bucket"
    key            = "uk49/rds/terraform.tfstate"
    region         = "us-east-1"
    encrypt        = true
    dynamodb_table = "terraform-locks"
  }
}
```

Then run:
```bash
terraform init
```

2. **Enable state locking** using DynamoDB to prevent concurrent edits.

## Monitoring & Alarms

CloudWatch alarms are created for production (`environment = "prod"`):
- **CPU Utilization**: Alert if > 75%
- **Free Storage**: Alert if < 2GB

To add SNS notifications, update `alarm_actions` in `main.tf`:
```hcl
alarm_actions = ["arn:aws:sns:us-east-1:123456789:my-alert-topic"]
```

## Cleanup

To destroy the RDS instance:

```bash
terraform destroy
```

**Warning**: This will delete the database. Make sure you have backups if you need the data.

If you previously ran with `skip_final_snapshot = true`, the final snapshot won't be created. Change to `false` before destroy if you want a backup:

```hcl
skip_final_snapshot = false
```

Then:
```bash
terraform destroy
```

## Troubleshooting

### "Error: IAM role does not have permission to perform"
Ensure your AWS credentials have:
- `rds:CreateDBInstance`, `rds:DeleteDBInstance`
- `ec2:CreateSecurityGroup`, `ec2:CreateVpc`
- `rds:DescribeDBInstances`, CloudWatch permissions

### "Error: DB instance is not in available state"
RDS is still initializing. Wait a few minutes and retry:
```bash
terraform plan
```

### "Publicly Accessible = false but I can't connect"
- Check your security group allows inbound on port 5432 from your CIDR
- Verify you're using the correct password
- If connecting from EC2, ensure the EC2 security group is in `allowed_cidr_blocks`

## Next Steps

1. **Create a backup** before using in production:
   ```bash
   aws rds create-db-snapshot --db-instance-identifier uk49-db-dev --db-snapshot-identifier uk49-backup-2026-02-15
   ```

2. **Test the connection** from your application:
   ```bash
   psql postgresql://uk49admin@uk49-db-dev.abc123def.us-east-1.rds.amazonaws.com/uk49
   ```

3. **Integrate into CI/CD** (optional):
   - Run `terraform plan` in pull requests
   - Run `terraform apply` on merge to main

## References

- [AWS RDS Terraform Docs](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance)
- [Terraform PostgreSQL Provider](https://registry.terraform.io/providers/hashicorp/postgresql/latest/docs)
