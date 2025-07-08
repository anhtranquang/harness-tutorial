.PHONY: install test build deploy clean

# Install dependencies
install:
	pip install -r requirements.txt

# Run local tests
test:
	python scripts/local_test.py

# Test specific environment
test-nonprod:
	ENV_NAME=NONPROD python src/main.py

test-prod:
	ENV_NAME=PROD python src/main.py

# Build Lambda package
build:
	python scripts/build.py

# Deploy with Terraform
deploy-nonprod:
	cd terraform && terraform apply -var="environment=NONPROD" -auto-approve

deploy-prod:
	cd terraform && terraform apply -var="environment=PROD" -auto-approve

# Clean build artifacts
clean:
	rm -rf build/
	rm -f lambda_function.zip
	rm -rf src/__pycache__/
	rm -rf tests/__pycache__/

# Run locally
run-local:
	ENV_NAME=NONPROD python src/main.py
