# variables.tf
variable "environment" {
  description = "Environment (NONPROD, PROD, DEV, etc.)"
  type        = string
  validation {
    condition     = contains(["NONPROD", "PROD", "DEV", "STAGING"], upper(var.environment))
    error_message = "Environment must be one of: NONPROD, PROD, DEV, STAGING"
  }
}

variable "additional_env_vars" {
  description = "Additional environment variables to add"
  type        = map(string)
  default     = {}
}

# locals.tf - Parse .env file and filter by environment
locals {
  # Read the .env file
  env_file = file("${path.module}/.env")
  
  # Parse all environment variables from .env file
  all_env_vars = {
    for line in compact(split("\n", local.env_file)) :
    trimspace(split("=", line)[0]) => trimspace(
      replace(
        replace(
          join("=", slice(split("=", line), 1, length(split("=", line)))),
          "\"", ""
        ),
        "'", ""
      )
    )
    if length(split("=", line)) >= 2 && !startswith(trimspace(line), "#") && trimspace(line) != ""
  }
  
  # Environment prefix (uppercase)
  env_prefix = "${upper(var.environment)}_"
  
  # Filter variables that start with the current environment prefix
  env_specific_vars = {
    for key, value in local.all_env_vars :
    key => value
    if startswith(key, local.env_prefix)
  }
  
  # Remove the environment prefix from variable names
  clean_env_vars = {
    for key, value in local.env_specific_vars :
    substr(key, length(local.env_prefix), -1) => value
  }
  
  # Final environment variables for Lambda
  lambda_env_vars = merge(
    local.clean_env_vars,
    var.additional_env_vars,
    {
      ENVIRONMENT = var.environment
      AWS_REGION  = data.aws_region.current.name
      DEPLOYED_AT = timestamp()
    }
  )
}

# main.tf - Lambda function with environment-specific variables
resource "aws_lambda_function" "python_lambda" {
  filename         = "lambda_function.zip"
  function_name    = "python-lambda-${lower(var.environment)}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "main.handler"
  runtime         = "python3.9"
  timeout         = 30
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = local.lambda_env_vars
  }

  depends_on = [
    aws_iam_role_policy_attachment.lambda_logs,
    aws_cloudwatch_log_group.lambda_logs,
  ]

  tags = {
    Environment = var.environment
    ManagedBy   = "Terraform"
  }
}

# Package the Lambda function
data "archive_file" "lambda_zip" {
  type        = "zip"
  source_dir  = "${path.module}/lambda_src"
  output_path = "${path.module}/lambda_function.zip"
  
  excludes = [".env", "__pycache__", "*.pyc", ".git", "*.md"]
}

# CloudWatch log group
resource "aws_cloudwatch_log_group" "lambda_logs" {
  name              = "/aws/lambda/python-lambda-${lower(var.environment)}"
  retention_in_days = var.environment == "PROD" ? 30 : 14
}

# IAM role for Lambda
resource "aws_iam_role" "lambda_role" {
  name = "lambda-role-${lower(var.environment)}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_role.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Alternative approach using for_each for multiple environments
# This creates separate Lambda functions for each environment
locals {
  environments = ["NONPROD", "PROD"]
  
  # Create environment-specific variables for each environment
  env_vars_by_environment = {
    for env in local.environments :
    env => {
      for key, value in local.all_env_vars :
      substr(key, length("${env}_"), -1) => value
      if startswith(key, "${env}_")
    }
  }
}

# Multiple Lambda functions (one per environment)
resource "aws_lambda_function" "multi_env_lambda" {
  for_each = toset(local.environments)
  
  filename         = "lambda_function.zip"
  function_name    = "python-lambda-${lower(each.key)}"
  role            = aws_iam_role.multi_env_lambda_role[each.key].arn
  handler         = "main.handler"
  runtime         = "python3.9"
  timeout         = 30
  source_code_hash = data.archive_file.lambda_zip.output_base64sha256

  environment {
    variables = merge(
      local.env_vars_by_environment[each.key],
      {
        ENVIRONMENT = each.key
        AWS_REGION  = data.aws_region.current.name
      }
    )
  }

  tags = {
    Environment = each.key
    ManagedBy   = "Terraform"
  }
}

# IAM roles for multiple environments
resource "aws_iam_role" "multi_env_lambda_role" {
  for_each = toset(local.environments)
  
  name = "lambda-role-${lower(each.key)}"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "multi_env_lambda_logs" {
  for_each = toset(local.environments)
  
  role       = aws_iam_role.multi_env_lambda_role[each.key].name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# Data sources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}

# Outputs
output "lambda_function_name" {
  value = aws_lambda_function.python_lambda.function_name
}

output "lambda_function_arn" {
  value = aws_lambda_function.python_lambda.arn
}

output "filtered_env_vars" {
  description = "Environment variables after filtering and cleaning"
  value       = local.clean_env_vars
  sensitive   = true
}

output "all_parsed_vars" {
  description = "All parsed variables from .env file"
  value       = keys(local.all_env_vars)
}

output "env_vars_by_environment" {
  description = "Variables grouped by environment"
  value       = { for env, vars in local.env_vars_by_environment : env => keys(vars) }
}

# Example .env file structure:
# # Non-production environment variables
# NONPROD_URL=https://api-dev.example.com
# NONPROD_API_KEY=dev-api-key-123
# NONPROD_DATABASE_URL=postgresql://dev-user:dev-pass@dev-db:5432/dev_db
# NONPROD_DEBUG=true
# NONPROD_LOG_LEVEL=DEBUG
# NONPROD_MAX_RETRIES=5
# NONPROD_TIMEOUT=60
# 
# # Production environment variables
# PROD_URL=https://api.example.com
# PROD_API_KEY=prod-api-key-456
# PROD_DATABASE_URL=postgresql://prod-user:prod-pass@prod-db:5432/prod_db
# PROD_DEBUG=false
# PROD_LOG_LEVEL=INFO
# PROD_MAX_RETRIES=3
# PROD_TIMEOUT=30
# 
# # Development environment variables
# DEV_URL=https://api-local.example.com
# DEV_API_KEY=dev-local-key-789
# DEV_DATABASE_URL=postgresql://localhost:5432/local_db
# DEV_DEBUG=true
# DEV_LOG_LEVEL=DEBUG
# 
# # Staging environment variables
# STAGING_URL=https://api-staging.example.com
# STAGING_API_KEY=staging-api-key-101
# STAGING_DATABASE_URL=postgresql://staging-user:staging-pass@staging-db:5432/staging_db
# STAGING_DEBUG=false
# STAGING_LOG_LEVEL=INFO

# terraform.tfvars examples:
# For NONPROD deployment:
# environment = "NONPROD"
# additional_env_vars = {
#   CUSTOM_VAR = "nonprod-custom-value"
# }
#
# For PROD deployment:
# environment = "PROD"
# additional_env_vars = {
#   CUSTOM_VAR = "prod-custom-value"
# }

# Usage examples:
# terraform apply -var="environment=NONPROD"
# terraform apply -var="environment=PROD"
# terraform apply -var-file="nonprod.tfvars"
# terraform apply -var-file="prod.tfvars"