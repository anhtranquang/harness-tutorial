# config.py - Environment configuration handler
import os
from typing import Dict, Optional
from dotenv import load_dotenv

class EnvironmentConfig:
    def __init__(self, environment: str = None):
        """
        Initialize environment configuration
        
        Args:
            environment: Environment name (NONPROD, PROD, DEV, etc.)
                        If None, will try to get from ENV_NAME or default to NONPROD
        """
        # Load .env file if it exists
        load_dotenv()
        
        # Determine environment
        self.environment = (
            environment or 
            os.getenv('ENV_NAME', 'NONPROD')
        ).upper()
        
        # Check if we're running in Lambda (AWS environment)
        self.is_lambda = self._is_running_in_lambda()
        
        # Load environment variables
        self.env_vars = self._load_environment_variables()
    
    def _is_running_in_lambda(self) -> bool:
        """Check if code is running in AWS Lambda environment"""
        return (
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None or
            os.getenv('LAMBDA_RUNTIME_DIR') is not None
        )
    
    def _load_environment_variables(self) -> Dict[str, str]:
        """Load and process environment variables based on context"""
        if self.is_lambda:
            # In Lambda, variables are already clean (no prefixes)
            return dict(os.environ)
        else:
            # In local environment, filter by prefix and clean names
            return self._filter_and_clean_env_vars()
    
    def _filter_and_clean_env_vars(self) -> Dict[str, str]:
        """Filter variables by environment prefix and remove prefix"""
        env_prefix = f"{self.environment}_"
        clean_vars = {}
        
        for key, value in os.environ.items():
            if key.startswith(env_prefix):
                # Remove prefix from key name
                clean_key = key[len(env_prefix):]
                clean_vars[clean_key] = value
        
        return clean_vars
    
    def get(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Get environment variable value"""
        return self.env_vars.get(key, default)
    
    def get_required(self, key: str) -> str:
        """Get required environment variable (raises error if not found)"""
        value = self.get(key)
        if value is None:
            raise ValueError(f"Required environment variable '{key}' not found")
        return value
    
    def get_bool(self, key: str, default: bool = False) -> bool:
        """Get boolean environment variable"""
        value = self.get(key)
        if value is None:
            return default
        return value.lower() in ('true', '1', 'yes', 'on')
    
    def get_int(self, key: str, default: int = 0) -> int:
        """Get integer environment variable"""
        value = self.get(key)
        if value is None:
            return default
        try:
            return int(value)
        except ValueError:
            return default
    
    def debug_info(self) -> Dict:
        """Get debug information about current configuration"""
        return {
            'environment': self.environment,
            'is_lambda': self.is_lambda,
            'available_vars': list(self.env_vars.keys()),
            'aws_region': self.get('AWS_REGION'),
            'function_name': os.getenv('AWS_LAMBDA_FUNCTION_NAME')
        }

# Create a global config instance
config = EnvironmentConfig()

# main.py - Your Lambda function
import json
import logging
from config import config

# Set up logging
logging.basicConfig(level=getattr(logging, config.get('LOG_LEVEL', 'INFO')))
logger = logging.getLogger(__name__)

def handler(event, context):
    """Lambda handler function"""
    try:
        # Get configuration values (works both locally and in Lambda)
        api_url = config.get_required('URL')
        api_key = config.get_required('API_KEY')
        database_url = config.get_required('DATABASE_URL')
        debug_mode = config.get_bool('DEBUG', False)
        max_retries = config.get_int('MAX_RETRIES', 3)
        timeout = config.get_int('TIMEOUT', 30)
        
        # Log configuration (only in debug mode)
        if debug_mode:
            logger.debug(f"Configuration: {config.debug_info()}")
        
        # Your business logic here
        response_data = {
            'message': 'Hello from Lambda!',
            'environment': config.environment,
            'api_url': api_url,
            'debug_mode': debug_mode,
            'max_retries': max_retries,
            'timeout': timeout,
            'is_lambda': config.is_lambda
        }
        
        return {
            'statusCode': 200,
            'headers': {
                'Content-Type': 'application/json',
                'Access-Control-Allow-Origin': '*'
            },
            'body': json.dumps(response_data)
        }
        
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': f'Configuration error: {str(e)}'})
        }
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({'error': 'Internal server error'})
        }

# local_test.py - Local testing script
import os
import sys
import json
from config import EnvironmentConfig

def test_local_environment():
    """Test the environment configuration locally"""
    
    # Test different environments
    environments = ['NONPROD', 'PROD', 'DEV']
    
    for env in environments:
        print(f"\n{'='*50}")
        print(f"Testing {env} Environment")
        print(f"{'='*50}")
        
        # Create config for specific environment
        env_config = EnvironmentConfig(environment=env)
        
        # Print debug info
        debug_info = env_config.debug_info()
        print(f"Environment: {debug_info['environment']}")
        print(f"Is Lambda: {debug_info['is_lambda']}")
        print(f"Available variables: {debug_info['available_vars']}")
        
        # Test getting variables
        try:
            print(f"URL: {env_config.get('URL')}")
            print(f"API_KEY: {env_config.get('API_KEY')}")
            print(f"DATABASE_URL: {env_config.get('DATABASE_URL')}")
            print(f"DEBUG: {env_config.get_bool('DEBUG')}")
            print(f"LOG_LEVEL: {env_config.get('LOG_LEVEL')}")
            print(f"MAX_RETRIES: {env_config.get_int('MAX_RETRIES')}")
            print(f"TIMEOUT: {env_config.get_int('TIMEOUT')}")
        except ValueError as e:
            print(f"Error: {e}")

def test_lambda_handler():
    """Test the Lambda handler function locally"""
    print(f"\n{'='*50}")
    print("Testing Lambda Handler")
    print(f"{'='*50}")
    
    # Set environment for testing
    os.environ['ENV_NAME'] = 'NONPROD'  # or 'PROD'
    
    # Import and test handler
    from main import handler
    
    # Mock event and context
    test_event = {
        'httpMethod': 'GET',
        'path': '/test',
        'queryStringParameters': None,
        'body': None
    }
    
    class MockContext:
        def __init__(self):
            self.function_name = 'test-function'
            self.memory_limit_in_mb = 128
            self.invoked_function_arn = 'arn:aws:lambda:us-east-1:123456789012:function:test'
            self.aws_request_id = 'test-request-id'
    
    # Call handler
    response = handler(test_event, MockContext())
    
    print("Response:")
    print(json.dumps(response, indent=2))

if __name__ == "__main__":
    # Test environment configuration
    test_local_environment()
    
    # Test Lambda handler
    test_lambda_handler()

# requirements.txt
# python-dotenv>=0.19.0
# boto3>=1.26.0

# .env file example (same as before):
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

# run_local.py - Simple local runner
import os
from main import handler

# Set environment for local testing
os.environ['ENV_NAME'] = 'NONPROD'  # Change to 'PROD' for prod testing

# Mock event and context for local testing
event = {'test': 'data'}
context = type('MockContext', (), {
    'function_name': 'local-test',
    'aws_request_id': 'local-test-id'
})()

# Run the handler
if __name__ == "__main__":
    result = handler(event, context)
    print("Local test result:")
    print(result)