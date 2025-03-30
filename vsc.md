# DevOps VS Code Setup Guide

This guide provides instructions for setting up Visual Studio Code with the necessary extensions and configurations for DevOps engineers working with Terraform modules in our organization.

## Table of Contents
- [Overview](#overview)
- [Required Extensions](#required-extensions)
- [Configuration Setup](#configuration-setup)
- [How Extensions Improve Module Development](#how-extensions-improve-module-development)
  - [Terraform Development](#terraform-development)
  - [Python Automation](#python-automation)
  - [YAML Configuration](#yaml-configuration)
  - [Shell Scripting](#shell-scripting)
  - [Markdown Documentation](#markdown-documentation)
  - [Spell Checking](#spell-checking)
- [Workflow Integration](#workflow-integration)
- [Troubleshooting](#troubleshooting)
- [Best Practices](#best-practices)

## Overview

To ensure consistent code quality and formatting across all Terraform module development, our DevOps team uses a standardized VS Code setup. This setup includes essential extensions for Terraform, Python, YAML, Shell, Markdown formatting, and spell checking, along with pre-configured settings that enforce our organization's coding standards.

## Required Extensions

Install the following extensions from the VS Code marketplace:

### Terraform Extensions
- [HashiCorp Terraform](https://marketplace.visualstudio.com/items?itemName=HashiCorp.terraform) - Official extension for Terraform language support
- [Terraform Doc Snippets](https://marketplace.visualstudio.com/items?itemName=run-at-scale.terraform-doc-snippets) - Templates for Terraform documentation

### Python Extensions
- [Python](https://marketplace.visualstudio.com/items?itemName=ms-python.python) - Main Python extension for VS Code
- [Pylint](https://marketplace.visualstudio.com/items?itemName=ms-python.pylint) - Python code analysis
- [Black Formatter](https://marketplace.visualstudio.com/items?itemName=ms-python.black-formatter) - Python code formatting

### YAML Extensions
- [YAML](https://marketplace.visualstudio.com/items?itemName=redhat.vscode-yaml) - YAML language support
- [YAML Sort](https://marketplace.visualstudio.com/items?itemName=PascalReitermann93.vscode-yaml-sort) - Sorting YAML files

### Shell Extensions
- [ShellCheck](https://marketplace.visualstudio.com/items?itemName=timonwong.shellcheck) - Shell script linting
- [Shell Format](https://marketplace.visualstudio.com/items?itemName=foxundermoon.shell-format) - Shell script formatting

### Markdown Extensions
- [Markdown All in One](https://marketplace.visualstudio.com/items?itemName=yzhang.markdown-all-in-one) - Writing and editing Markdown
- [markdownlint](https://marketplace.visualstudio.com/items?itemName=DavidAnson.vscode-markdownlint) - Markdown linting

### Other Essential Extensions
- [Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker) - Catch common spelling mistakes
- [Prettier - Code formatter](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) - Consistent code formatting
- [Material Icon Theme](https://marketplace.visualstudio.com/items?itemName=PKief.material-icon-theme) - Improved file icons for better visibility
- [GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens) - Git integration and history visualization

You can install all extensions at once using the following command in your terminal:

```bash
code --install-extension HashiCorp.terraform \
     --install-extension run-at-scale.terraform-doc-snippets \
     --install-extension ms-python.python \
     --install-extension ms-python.pylint \
     --install-extension ms-python.black-formatter \
     --install-extension redhat.vscode-yaml \
     --install-extension PascalReitermann93.vscode-yaml-sort \
     --install-extension timonwong.shellcheck \
     --install-extension foxundermoon.shell-format \
     --install-extension yzhang.markdown-all-in-one \
     --install-extension DavidAnson.vscode-markdownlint \
     --install-extension streetsidesoftware.code-spell-checker \
     --install-extension esbenp.prettier-vscode \
     --install-extension PKief.material-icon-theme \
     --install-extension eamodio.gitlens
```

## Configuration Setup

### Method 1: User Settings (For Individual Developers)

1. Open VS Code
2. Press `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac) to open the Command Palette
3. Type "Preferences: Open Settings (JSON)" and select it
4. Copy and paste the contents of the `settings.json` file below into your user settings
5. Save the file

### Method 2: Workspace Settings (For Team-wide Settings)

1. In your project's root directory, create a `.vscode` folder if it doesn't exist already
2. Create a file named `settings.json` within this folder
3. Copy and paste the contents below into this file
4. Commit and push these changes to your repository

### settings.json

```json
{
  // Editor settings
  "editor.formatOnSave": true,
  "editor.tabSize": 2,
  "editor.rulers": [80, 120],
  "editor.renderWhitespace": "boundary",
  "editor.codeActionsOnSave": {
    "source.fixAll": true
  },
  "editor.bracketPairColorization.enabled": true,
  "editor.guides.bracketPairs": true,
  "editor.suggestSelection": "first",
  "editor.wordWrap": "off",
  "editor.detectIndentation": false,
  "editor.insertSpaces": true,
  
  // File associations
  "files.associations": {
    "*.tf": "terraform",
    "*.tfvars": "terraform",
    "*.tfbackend": "terraform"
  },
  "files.trimTrailingWhitespace": true,
  "files.insertFinalNewline": true,
  
  // Terraform settings
  "terraform.languageServer": {
    "enabled": true,
    "args": []
  },
  "terraform.indexing": {
    "enabled": true,
    "liveIndexing": true
  },
  "terraform.format": {
    "enable": true,
    "ignoreExtensionsOnSave": [".tfvars"],
    "formatOnSave": true
  },
  "terraform.experimentalFeatures.validateOnSave": true,
  "terraform.experimentalFeatures.prefillRequiredFields": true,
  
  // Set default formatters for different file types
  "[terraform]": {
    "editor.defaultFormatter": "hashicorp.terraform"
  },
  "[terraform-vars]": {
    "editor.defaultFormatter": "hashicorp.terraform"
  },
  "[json]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[jsonc]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[markdown]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[yaml]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  },
  "[python]": {
    "editor.defaultFormatter": "ms-python.black-formatter"
  },
  "[shellscript]": {
    "editor.defaultFormatter": "foxundermoon.shell-format"
  },
  
  // Markdown settings
  "markdown.preview.breaks": true,
  "markdown.extension.toc.levels": "2..3",
  "markdown.extension.toc.updateOnSave": true,
  "markdown.extension.orderedList.marker": "ordered",
  "markdown.extension.tableFormatter.enabled": true,
  "markdownlint.config": {
    "MD013": false,
    "MD024": false,
    "MD033": false
  },
  
  // Python settings
  "python.linting.enabled": true,
  "python.linting.pylintEnabled": true,
  "python.linting.flake8Enabled": true,
  "python.linting.flake8Args": [
    "--max-line-length=120",
    "--ignore=E203,W503"
  ],
  "python.formatting.provider": "black",
  "python.formatting.blackArgs": [
    "--line-length=120"
  ],
  "python.testing.pytestEnabled": true,
  
  // YAML settings
  "yaml.format.enable": true,
  "yaml.validate": true,
  "yaml.schemas": {
    "https://json.schemastore.org/github-workflow.json": ".github/workflows/*.yml",
    "https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json": "*docker-compose*.yml"
  },
  
  // Shell script settings
  "shellcheck.enable": true,
  "shellcheck.useWorkspaceRootAsCwd": true,
  "shellcheck.run": "onSave",
  
  // Prettier settings
  "prettier.singleQuote": true,
  "prettier.tabWidth": 2,
  "prettier.printWidth": 120,
  "prettier.trailingComma": "es5",
  "prettier.semi": true,
  
  // Code Spell Checker settings
  "cSpell.enabled": true,
  "cSpell.language": "en",
  "cSpell.words": [
    "tfvars",
    "tfstate",
    "tfbackend",
    "terrraform",
    "hashicorp",
    "pylint",
    "flake8",
    "pytest",
    "boto3",
    "cloudformation",
    "kubectl",
    "kubernetes",
    "eksctl"
  ],
  "cSpell.enableFiletypes": [
    "terraform",
    "markdown",
    "python",
    "yaml",
    "json",
    "shellscript"
  ],
  "cSpell.ignorePaths": [
    ".git",
    ".terraform",
    "node_modules"
  ],
  
  // Terminal settings
  "terminal.integrated.defaultProfile.linux": "bash",
  "terminal.integrated.defaultProfile.windows": "PowerShell",
  "terminal.integrated.defaultProfile.osx": "zsh",
  
  // Git settings
  "git.enableSmartCommit": true,
  "git.confirmSync": false,
  "git.autofetch": true,
  "gitlens.codeLens.enabled": true,
  
  // Workspace settings
  "workbench.colorTheme": "Default Dark+",
  "workbench.iconTheme": "material-icon-theme",
  "workbench.editor.highlightModifiedTabs": true,
  "workbench.editor.revealIfOpen": true,
  
  // Telemetry settings
  "telemetry.telemetryLevel": "off"
}
```

## How Extensions Improve Module Development

### Terraform Development

The Terraform extensions provide real-time validation, auto-completion, and formatting that significantly improve module development:

#### Example: Auto-completion and validation

```terraform
resource "aws_s3_bucket" "logs" {
  bucket = "${var.project_name}-logs-${var.environment}"
  
  # The extension suggests available properties with documentation
  versioning {
    enabled = true
  }
  
  # Catch validation errors before committing
  lifecycle_rule {
    id      = "log-rotation"
    enabled = true
    
    expiration {
      days = 90
    }
  }
  
  tags = var.common_tags
}
```

**Benefits:**
- **Auto-completion** suggests resource types and their properties
- **Syntax highlighting** makes code more readable
- **Real-time validation** identifies errors as you type
- **Format on save** ensures consistent code style

#### Example: Module documentation with snippets

```terraform
/**
 * # S3 Logs Bucket Module
 *
 * This module creates an S3 bucket configured for logging with appropriate lifecycle policies.
 *
 * ## Usage
 * ```hcl
 * module "logs_bucket" {
 *   source      = "./modules/s3_logs_bucket"
 *   project_name = "acme"
 *   environment = "prod"
 * }
 * ```
 */

variable "project_name" {
  description = "Name of the project"
  type        = string
}

variable "environment" {
  description = "Deployment environment (dev, staging, prod)"
  type        = string
}
```

**Benefits:**
- **Doc snippets** generate standardized documentation templates
- **Auto-formatting** of comments and documentation

### Python Automation

Python is often used to automate Terraform tasks and validate infrastructure. The extensions ensure code quality:

#### Example: Terraform output validator

```python
def validate_terraform_outputs(output_file, required_outputs):
    """
    Validates that required outputs exist in Terraform output file.
    
    Args:
        output_file (str): Path to terraform output JSON file
        required_outputs (list): List of required output names
    
    Returns:
        bool: True if all required outputs exist
    """
    try:
        with open(output_file, 'r') as f:
            outputs = json.load(f)
            
        missing_outputs = []
        for output in required_outputs:
            if output not in outputs:
                missing_outputs.append(output)
                
        if missing_outputs:
            print(f"Missing required outputs: {', '.join(missing_outputs)}")
            return False
            
        return True
    except Exception as e:
        print(f"Error validating outputs: {str(e)}")
        return False
```

**Benefits:**
- **Code linting** identifies potential bugs
- **Auto-formatting** with Black ensures consistent style
- **Type hints** improve code readability
- **Documentation help** with docstring formatting

### YAML Configuration

YAML is essential for CI/CD pipelines and configuration files in infrastructure:

#### Example: GitHub Actions workflow

```yaml
name: 'Terraform Module Validation'

on:
  pull_request:
    paths:
      - 'modules/**/*.tf'
      - '.github/workflows/terraform-validate.yml'

jobs:
  validate:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v3
        
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v2
        with:
          terraform_version: 1.5.0
          
      - name: Terraform Init
        run: |
          for module in $(find modules -name "*.tf" -exec dirname {} \; | sort -u); do
            echo "Initializing $module"
            cd $module
            terraform init -backend=false
            cd -
          done
          
      - name: Terraform Validate
        run: |
          for module in $(find modules -name "*.tf" -exec dirname {} \; | sort -u); do
            echo "Validating $module"
            cd $module
            terraform validate
            cd -
          done
```

**Benefits:**
- **Schema validation** ensures workflow files are correctly structured
- **Syntax highlighting** makes YAML more readable
- **Auto-formatting** ensures consistent indentation
- **YAML sorting** organizes complex configuration files

### Shell Scripting

Shell scripts automate deployment workflows and module testing:

#### Example: Module testing script

```bash
#!/bin/bash

# Validate Terraform modules in the repo
# Usage: ./validate_modules.sh [module_path]

set -e

# Check if terraform is installed
if ! command -v terraform &> /dev/null; then
    echo "Terraform not found. Please install Terraform first."
    exit 1
fi

# Determine which modules to validate
if [ -z "$1" ]; then
    # Find all modules
    modules=$(find . -name "main.tf" -exec dirname {} \; | sort -u)
else
    # Validate specific module
    modules=$1
fi

# Initialize and validate each module
for module in $modules; do
    echo "================================================================"
    echo "Validating module: $module"
    echo "================================================================"
    
    pushd "$module" > /dev/null
    
    # Initialize without backend
    terraform init -backend=false
    
    # Validate syntax
    terraform validate
    
    # Check formatting
    terraform fmt -check || echo "WARNING: Formatting issues found"
    
    popd > /dev/null
    echo ""
done

echo "All modules validated successfully!"
```

**Benefits:**
- **ShellCheck** identifies common shell script issues
- **Syntax highlighting** improves readability
- **Auto-formatting** ensures consistent spacing and indentation
- **Error detection** finds issues before execution

### Markdown Documentation

Quality documentation is crucial for module reusability:

#### Example: Module README.md

```markdown
# AWS S3 Secure Bucket Module

## Overview

This Terraform module creates a secure S3 bucket with encryption, versioning, and proper access controls following best practices.

## Usage

```terraform
module "secure_bucket" {
  source      = "./modules/s3_secure_bucket"
  bucket_name = "my-secure-data"
  environment = "production"
  
  # Optional configurations
  versioning_enabled = true
  
  tags = {
    Department = "Finance"
    Project    = "Data Warehouse"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| bucket_name | Name of the S3 bucket | `string` | n/a | yes |
| environment | Deployment environment | `string` | n/a | yes |
| versioning_enabled | Enable versioning for the bucket | `bool` | `true` | no |
| tags | Resource tags | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| bucket_id | The name of the bucket |
| bucket_arn | The ARN of the bucket |
| bucket_domain_name | The bucket domain name |
```

**Benefits:**
- **Table formatting** automatically aligns tables
- **TOC generation** creates navigation for long documents
- **Link validation** ensures all references work
- **Preview** shows final rendered output
- **Linting** enforces consistent style

### Spell Checking

Consistent spelling improves professionalism in code and documentation:

#### Example: With and without spell checking

**Before:**
```terraform
resource "aws_iam_polcy" "s3_acess" {
  name        = "s3-bucket-acess-policy"
  description = "Policy that grants permisions to the logging buckt"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:GetObject", "s3:PutObjet"]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.logging_buckt.arn}/*"
      }
    ]
  })
}
```

**After (with spell checking):**
```terraform
resource "aws_iam_policy" "s3_access" {
  name        = "s3-bucket-access-policy"
  description = "Policy that grants permissions to the logging bucket"
  
  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action   = ["s3:GetObject", "s3:PutObject"]
        Effect   = "Allow"
        Resource = "${aws_s3_bucket.logging_bucket.arn}/*"
      }
    ]
  })
}
```

**Benefits:**
- **Highlights typos** in resource names and descriptions
- **Technical terminology** is recognized with custom dictionary
- **Reduces confusion** in shared code
- **Improves searchability** of code and documentation

## Workflow Integration

These extensions work together to create a seamless development workflow:

1. **Start new module**:
   - Use Terraform snippets to generate module structure
   - Auto-completion helps with resource attributes
   - Doc snippets create standardized README

2. **Development cycle**:
   - Real-time validation catches errors as you type
   - On-save formatting maintains consistent style
   - Spell checker prevents typos in variable names
   - ShellCheck validates test scripts

3. **Documentation**:
   - Markdown extensions format module documentation
   - Table formatter aligns input/output tables
   - Spell checker ensures professional documentation

4. **CI/CD Pipeline**:
   - YAML validation ensures proper workflow files
   - Python linting keeps automation scripts clean
   - Markdown lint prevents broken documentation

## Troubleshooting

### Common Issues

1. **Terraform formatting doesn't work**
   - Ensure the Terraform CLI is installed and in your PATH
   - Run `terraform --version` in your terminal to verify

2. **Python linting shows too many errors**
   - Install required dependencies: `pip install pylint flake8 black`
   - Create a `.pylintrc` file in your project to customize rules

3. **Extensions not loading properly**
   - Try reloading VS Code (`Ctrl+R` or `Cmd+R`)
   - Check the Extensions view for any error messages

4. **Settings not applying**
   - User settings may override workspace settings
   - Check which settings are active by using "Preferences: Open Default Settings (JSON)"

5. **ShellCheck reporting false positives**
   - Add `# shellcheck disable=SC2034` to suppress specific warnings
   - Configure exclusions in the settings.json file

### Getting Help

If you encounter issues that aren't resolved by the troubleshooting steps above:
1. Check the extension's documentation on the VS Code Marketplace
2. Reach out to the DevOps team lead
3. File an issue in the team's internal support repository

## Best Practices

1. **Always pull the latest settings**
   - The workspace settings may be updated periodically, so pull the latest changes before starting work

2. **Use keyboard shortcuts**
   - Format document: `Shift+Alt+F`
   - Open command palette: `Ctrl+Shift+P` (Windows/Linux) or `Cmd+Shift+P` (Mac)
   - Toggle terminal: ``Ctrl+` ``
   - Quick file navigation: `Ctrl+P`

3. **Commit early and often**
   - With automatic linting and formatting, your code will always be in a committable state

4. **Modularize your Terraform code**
   - Create small, focused modules with clear documentation
   - Use consistent variable and output naming conventions

5. **Document as you code**
   - Write documentation alongside the code, not after
   - Use the Markdown preview to ensure documentation looks good

6. **Contribute to our extensions list**
   - If you find a useful extension, suggest it to the team for inclusion in our standard setup

---

This setup guide was last updated on March 30, 2025. If you find any discrepancies or have suggestions for improvements, please contact the DevOps team.
