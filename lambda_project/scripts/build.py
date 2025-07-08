import os
import sys
import json
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from config import EnvironmentConfig

def test_environments():
    """Test different environments"""
    environments = ['NONPROD', 'PROD', 'DEV']
    
    for env in environments:
        print(f"\n{'='*60}")
        print(f"Testing {env} Environment")
        print(f"{'='*60}")
        
        try:
            # Create config for specific environment
            env_config = EnvironmentConfig(environment=env)
            
            # Print debug info
            debug_info = env_config.debug_info()
            print(f"Environment: {debug_info['environment']}")
            print(f"Is Lambda: {debug_info['is_lambda']}")
            print(f"Available variables: {debug_info['available_vars']}")
            
            # Test getting variables
            print(f"URL: {env_config.get('URL')}")
            print(f"API_KEY: {env_config.get('API_KEY')}")
            print(f"DATABASE_URL: {env_config.get('DATABASE_URL')}")
            print(f"DEBUG: {env_config.get_bool('DEBUG')}")
            print(f"LOG_LEVEL: {env_config.get('LOG_LEVEL')}")
            print(f"MAX_RETRIES: {env_config.get_int('MAX_RETRIES')}")
            print(f"TIMEOUT: {env_config.get_int('TIMEOUT')}")
            
        except Exception as e:
            print(f"Error testing {env}: {e}")

def test_lambda_handler():
    """Test Lambda handler locally"""
    print(f"\n{'='*60}")
    print("Testing Lambda Handler")
    print(f"{'='*60}")
    
    # Test with different environments
    for env in ['NONPROD', 'PROD']:
        print(f"\n--- Testing {env} ---")
        os.environ['ENV_NAME'] = env
        
        # Import main (this will reload config with new environment)
        from main import handler
        
        # Mock context
        class MockContext:
            def __init__(self):
                self.function_name = f'test-function-{env.lower()}'
                self.aws_request_id = f'test-request-{env.lower()}'
                self.memory_limit_in_mb = 128
        
        # Test event
        test_event = {'httpMethod': 'GET', 'path': '/test'}
        
        # Call handler
        response = handler(test_event, MockContext())
        
        print("Response:")
        print(json.dumps(response, indent=2))

if __name__ == "__main__":
    test_environments()
    test_lambda_handler()
