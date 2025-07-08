locals {
  # Read the .env file from parent directory
  env_file = file("${path.module}/../.env")
  
  # Parse environment variables
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
  
  # Environment prefix
  env_prefix = "${upper(var.environment)}_"
  
  # Filter and clean environment variables
  clean_env_vars = {
    for key, value in local.all_env_vars :
    substr(key, length(local.env_prefix), -1) => value
    if startswith(key, local.env_prefix)
  }
  
  # Final Lambda environment variables
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

# Lambda function
resource "aws_lambda_function" "python_lambda" {
  filename         = "../lambda_function.zip"
  function_name    = "python-lambda-${lower(var.environment)}"
  role            = aws_iam_role.lambda_role.arn
  handler         = "src.main.handler"  # Updated handler path
  runtime         = "python3.9"
  timeout         = 30
  source_code_hash = filebase64sha256("../lambda_function.zip")

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