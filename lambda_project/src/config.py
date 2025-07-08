import os
from typing import Dict, Optional
from pathlib import Path

class EnvironmentConfig:
    def __init__(self, environment: str = None, root_dir: str = None):
        """
        Initialize environment configuration
        
        Args:
            environment: Environment name (NONPROD, PROD, DEV, etc.)
            root_dir: Root directory for finding .env file (auto-detected if None)
        """
        # Auto-detect root directory
        if root_dir is None:
            root_dir = self._find_project_root()
        
        # Load .env file if it exists (only for local development)
        if not self._is_running_in_lambda():
            self._load_dotenv(root_dir)
        
        # Determine environment
        self.environment = (
            environment or 
            os.getenv('ENV_NAME') or
            os.getenv('ENVIRONMENT', 'NONPROD')
        ).upper()
        
        # Check if we're running in Lambda
        self.is_lambda = self._is_running_in_lambda()
        
        # Load environment variables
        self.env_vars = self._load_environment_variables()
    
    def _find_project_root(self) -> str:
        """Find project root directory by looking for .env file"""
        current_dir = Path(__file__).parent
        
        # Look for .env file in current dir and parent dirs
        for parent in [current_dir] + list(current_dir.parents):
            if (parent / '.env').exists():
                return str(parent)
        
        # If not found, return current directory
        return str(current_dir.parent)
    
    def _load_dotenv(self, root_dir: str):
        """Load .env file using python-dotenv"""
        try:
            from dotenv import load_dotenv
            env_path = os.path.join(root_dir, '.env')
            if os.path.exists(env_path):
                load_dotenv(env_path)
        except ImportError:
            # python-dotenv not installed, manually load .env
            self._manual_load_dotenv(root_dir)
    
    def _manual_load_dotenv(self, root_dir: str):
        """Manually load .env file if python-dotenv is not available"""
        env_path = os.path.join(root_dir, '.env')
        if os.path.exists(env_path):
            with open(env_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        key = key.strip()
                        value = value.strip().strip('"').strip("'")
                        if key not in os.environ:  # Don't override existing env vars
                            os.environ[key] = value
    
    def _is_running_in_lambda(self) -> bool:
        """Check if code is running in AWS Lambda environment"""
        return (
            os.getenv('AWS_LAMBDA_FUNCTION_NAME') is not None or
            os.getenv('LAMBDA_RUNTIME_DIR') is not None or
            os.getenv('AWS_EXECUTION_ENV', '').startswith('AWS_Lambda')
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
            raise ValueError(f"Required environment variable '{key}' not found for environment '{self.environment}'")
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
            'function_name': os.getenv('AWS_LAMBDA_FUNCTION_NAME'),
            'runtime': os.getenv('AWS_EXECUTION_ENV')
        }

# Create a global config instance
config = EnvironmentConfig()