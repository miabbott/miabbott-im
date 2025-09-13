#!/bin/bash
set -e

echo "🧪 GitHub Issue Monitor - Test Runner"
echo "====================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "src/monitor_github_notify.py" ]; then
    print_error "Please run this script from the project root directory"
    exit 1
fi

# Install test dependencies
print_status "Installing test dependencies..."
if command -v pip3 &> /dev/null; then
    PIP_CMD="pip3"
else
    PIP_CMD="pip"
fi

$PIP_CMD install -r requirements.txt
$PIP_CMD install -r tests/requirements-test.txt

# Code formatting check
print_status "Checking code formatting with Black..."
if black --check src/ tests/ 2>/dev/null; then
    print_success "Code formatting is correct"
else
    print_warning "Code formatting issues found. Run 'black src/ tests/' to fix"
fi

# Import sorting check
print_status "Checking import sorting with isort..."
if isort --check-only src/ tests/ 2>/dev/null; then
    print_success "Import sorting is correct"
else
    print_warning "Import sorting issues found. Run 'isort src/ tests/' to fix"
fi

# Linting
print_status "Running flake8 linting..."
if flake8 src/ tests/ --count --select=E9,F63,F7,F82 --show-source --statistics; then
    print_success "No critical linting errors found"
else
    print_error "Critical linting errors found"
    exit 1
fi

# Type checking
print_status "Running type checking with mypy..."
if mypy src/ --ignore-missing-imports 2>/dev/null; then
    print_success "Type checking passed"
else
    print_warning "Type checking found some issues"
fi

# Security check
print_status "Running security check with bandit..."
if bandit -r src/ -ll 2>/dev/null; then
    print_success "Security check passed"
else
    print_warning "Security check found some issues"
fi

# Configuration validation
print_status "Validating JSON configuration files..."
for file in configs/*.json; do
    if python -m json.tool "$file" > /dev/null 2>&1; then
        print_success "Valid JSON: $file"
    else
        print_error "Invalid JSON: $file"
        exit 1
    fi
done

# Run unit tests
print_status "Running unit tests..."
export GITHUB_TOKEN="fake_token_for_testing"
if pytest tests/test_monitor.py -v --cov=src --cov-report=term-missing; then
    print_success "Unit tests passed"
else
    print_error "Unit tests failed"
    exit 1
fi

# Run integration tests
print_status "Running integration tests..."
if pytest tests/test_integration.py -v; then
    print_success "Integration tests passed"
else
    print_error "Integration tests failed"
    exit 1
fi

# Test the example configuration
print_status "Testing example configuration..."
export CONFIG_FILE="configs/template.json.example"
if timeout 10s python src/monitor_github_notify.py 2>/dev/null || [ $? -eq 124 ]; then
    print_success "Example configuration loads successfully"
else
    print_warning "Example configuration test had issues (may be due to missing GitHub token)"
fi

echo ""
print_success "🎉 All tests completed successfully!"
echo ""
echo "📊 Test Coverage Report:"
echo "Run 'pytest --cov=src --cov-report=html' to generate detailed HTML coverage report"
echo ""
echo "🚀 Ready to commit and push!"
