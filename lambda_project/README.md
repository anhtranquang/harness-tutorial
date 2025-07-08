# Lambda Project with Terraform

## Project Structure
- `src/` - Source code (shared between local and Lambda)
- `terraform/` - Terraform configuration
- `scripts/` - Utility scripts
- `tests/` - Test files

## Local Development
```bash
# Install dependencies
make install

# Test locally
make test

# Run specific environment
make test-nonprod
make test-prod
```

## Deployment
```bash
# Build Lambda package
make build

# Deploy to environments
make deploy-nonprod
make deploy-prod
```

## Environment Variables
All environment variables are stored in `.env` file with prefixes:
- `NONPROD_*` for non-production
- `PROD_*` for production


I'll create a unified project structure that works for both local development and Terraform deployment without duplication.This unified project structure eliminates duplication and works seamlessly for both local development and Terraform deployment. Here are the key improvements:

## 🎯 **Unified Structure Benefits:**

### ✅ **Single Source Code**
- `src/` directory contains all code used by both local and Lambda
- No duplication between `lambda_src/` and local files
- Same imports and paths everywhere

### ✅ **Smart Environment Detection**
- Automatically detects Lambda vs local environment
- Handles `.env` file loading only when needed
- Works with or without `python-dotenv`

### ✅ **Simplified Development Workflow**
```bash
# Local testing
make test-nonprod
make test-prod

# Build and deploy
make build
make deploy-nonprod
```

### ✅ **Consistent Paths**
- Terraform uses `src.main.handler` (same structure)
- Local testing uses same imports
- No path confusion

## 🔧 **Key Features:**

### **Smart Config Loading**
- Auto-finds project root by looking for `.env` file
- Loads `.env` only in local environment
- Uses clean variable names everywhere

### **Build Process**
- `scripts/build.py` packages `src/` for Lambda
- Terraform reads from parent directory
- No duplicate configuration files

### **Testing**
- `scripts/local_test.py` tests all environments
- `make test` runs comprehensive tests
- Same code runs locally and in Lambda

## 🚀 **Usage Examples:**

### **Local Development:**
```bash
# Test NONPROD locally
ENV_NAME=NONPROD python src/main.py

# Test PROD locally  
ENV_NAME=PROD python src/main.py
```

### **Deployment:**
```bash
# Build package
make build

# Deploy to NONPROD
cd terraform && terraform apply -var="environment=NONPROD"

# Deploy to PROD
cd terraform && terraform apply -var="environment=PROD"
```

### **The Magic:**
- **Local:** Reads `.env` with prefixes, strips them
- **Lambda:** Gets clean variables from Terraform
- **Same Code:** `config.get('URL')` works everywhere

This structure gives you:
- ✅ No code duplication
- ✅ Consistent environment handling
- ✅ Easy local testing
- ✅ Streamlined deployment
- ✅ Single source of truth for configuration

Perfect for professional development workflows!