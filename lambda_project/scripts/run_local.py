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