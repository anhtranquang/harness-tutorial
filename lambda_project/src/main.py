import json
import logging
from .config import config

# Set up logging
log_level = config.get('LOG_LEVEL', 'INFO')
logging.basicConfig(
    level=getattr(logging, log_level),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
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
        
        logger.info(f"Processing request in {config.environment} environment")
        
        # Your business logic here
        response_data = {
            'message': 'Hello from Lambda!',
            'environment': config.environment,
            'api_url': api_url,
            'debug_mode': debug_mode,
            'max_retries': max_retries,
            'timeout': timeout,
            'is_lambda': config.is_lambda,
            'timestamp': context.aws_request_id if hasattr(context, 'aws_request_id') else 'local-test'
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

# Local entry point for testing
if __name__ == "__main__":
    # Mock context for local testing
    class MockContext:
        def __init__(self):
            self.function_name = 'local-test'
            self.aws_request_id = 'local-test-id'
            self.memory_limit_in_mb = 128
    
    # Test event
    test_event = {'test': 'local'}
    test_context = MockContext()
    
    # Run handler
    result = handler(test_event, test_context)
    print(json.dumps(result, indent=2))
