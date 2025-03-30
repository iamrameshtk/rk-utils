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
  - [Google Cloud Development](#google-cloud-development)
  - [Security Controls Development](#security-controls-development)
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

### Google Cloud Extensions
- [Cloud Code](https://marketplace.visualstudio.com/items?itemName=GoogleCloudTools.cloudcode) - Tools for GCP development
- [GCP Resource Monitor](https://marketplace.visualstudio.com/items?itemName=cody-kochmann.gcp-resource-monitor) - Monitor GCP resources in real-time
- [Terraform Google Provider](https://marketplace.visualstudio.com/items?itemName=googlecloudtools.google) - Extension for Google Cloud provider support

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

### Security and Policy Extensions
- [Ruby](https://marketplace.visualstudio.com/items?itemName=rebornix.Ruby) - Ruby language support for Chef InSpec
- [Chef InSpec](https://marketplace.visualstudio.com/items?itemName=chef-software.chef-inspec) - InSpec code snippets and validation
- [Rego](https://marketplace.visualstudio.com/items?itemName=tsandall.opa) - Support for Open Policy Agent Rego language
- [Common Expression Language](https://marketplace.visualstudio.com/items?itemName=playtika.vscode-cel-extension) - CEL syntax highlighting and validation
- [Policy Controller](https://marketplace.visualstudio.com/items?itemName=GoogleCloudTools.policy-controller) - For GCP organization policy development

#### Example: Ruby/Chef InSpec Extension

**Before (Without Ruby/Chef InSpec Extensions):**
```ruby
control 'gcp-storage-buckets-encryption-1.0' do
impact 'high'
title 'Ensure all storage buckets use CMEK'
desc 'Storage buckets should be encrypted with Customer-Managed Encryption Keys'

google_storage_buckets(project: project_id).bucket_names.each do |bucket|
describe google_storage_bucket(name: bucket) do
its('encryption.default_kms_key_name') { should match /projects\/.*\/cryptoKeys\// }
end
end
end
```

**After (With Ruby/Chef InSpec Extensions):**
```ruby
control 'gcp-storage-buckets-encryption-1.0' do
  impact 'high'
  title 'Ensure all storage buckets use CMEK'
  desc 'Storage buckets should be encrypted with Customer-Managed Encryption Keys'

  google_storage_buckets(project: project_id).bucket_names.each do |bucket|
    describe google_storage_bucket(name: bucket) do
      its('encryption.default_kms_key_name') { should match /projects\/.*\/cryptoKeys\// }
    end
  end
end
```

**Benefits:**
- Proper indentation of Ruby code blocks
- Syntax highlighting specific to InSpec controls
- Auto-completion for InSpec resources
- Validation of InSpec control structure
- InSpec-specific snippets for common patterns

#### Example: Rego Extension for OPA

**Before (Without Rego Extension):**
```rego
package terraform.analysis

import input.plan as tfplan

# Deny GCS buckets without encryption configured
deny[msg] {
bucket := tfplan.resource_changes[_]
bucket.type == "google_storage_bucket"
bucket.change.after.encryption == null

msg := sprintf(
"Bucket %v does not have encryption configured",
[bucket.change.after.name]
)
}
```

**After (With Rego Extension):**
```rego
package terraform.analysis

import input.plan as tfplan

# Deny GCS buckets without encryption configured
deny[msg] {
  bucket := tfplan.resource_changes[_]
  bucket.type == "google_storage_bucket"
  bucket.change.after.encryption == null

  msg := sprintf(
    "Bucket %v does not have encryption configured",
    [bucket.change.after.name]
  )
}
```

**Benefits:**
- Proper indentation of Rego rules
- Syntax highlighting for Rego language constructs
- Auto-completion for Rego built-in functions
- Visual separation between logical blocks
- Rule validation against Rego language server

#### Example: CEL Extension

**Before (Without CEL Extension):**
```yaml
# Custom organization policy constraint
name: custom.requireBucketCMEK
description: Require all buckets to use CMEK
resourceTypes:
  - storage.googleapis.com/Bucket
methodTypes:
  - CREATE
  - UPDATE
condition:
  expression: "resource.encryption != null && resource.encryption.defaultKmsKeyName != null"
  title: "Require CMEK on all buckets"
```

**After (With CEL Extension):**
```yaml
# Custom organization policy constraint
name: custom.requireBucketCMEK
description: Require all buckets to use CMEK
resourceTypes:
  - storage.googleapis.com/Bucket
methodTypes:
  - CREATE
  - UPDATE
condition:
  expression: "has(resource.encryption) && has(resource.encryption.defaultKmsKeyName)"
  title: "Require CMEK on all buckets"
```

**Benefits:**
- Syntax highlighting for CEL expressions
- Validation of CEL expression syntax
- Error detection for invalid CEL functions
- CEL-specific syntax suggestions
- Integration with Google Cloud resource schema

#### Example: Policy Controller Extension

**Before (Without Policy Controller Extension):**
```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: GCPStorageCMEKConstraint
metadata:
  name: require-storage-cmek
spec:
  match:
    kinds:
    - apiGroups: ["storage.cnrm.cloud.google.com"]
      kinds: ["StorageBucket"]
  parameters:
    exemptedNamespaces: ["kube-system"]
```

**After (With Policy Controller Extension):**
```yaml
apiVersion: constraints.gatekeeper.sh/v1beta1
kind: GCPStorageCMEKConstraint
metadata:
  name: require-storage-cmek
spec:
  match:
    kinds:
      - apiGroups: ["storage.cnrm.cloud.google.com"]
        kinds: ["StorageBucket"]
  parameters:
    exemptedNamespaces: 
      - "kube-system"
```

**Benefits:**
- Proper YAML indentation for Kubernetes resources
- Validation against Gatekeeper constraint schema
- Integration with GCP resource types
- Namespace and resource kind validation
- Auto-completion for constraint parameters

### Other Essential Extensions
- [Code Spell Checker](https://marketplace.visualstudio.com/items?itemName=streetsidesoftware.code-spell-checker) - Catch common spelling mistakes
- [Prettier - Code formatter](https://marketplace.visualstudio.com/items?itemName=esbenp.prettier-vscode) - Consistent code formatting
- [Material Icon Theme](https://marketplace.visualstudio.com/items?itemName=PKief.material-icon-theme) - Improved file icons for better visibility
- [GitLens](https://marketplace.visualstudio.com/items?itemName=eamodio.gitlens) - Git integration and history visualization

You can install all extensions at once using the following command in your terminal:

```bash
code --install-extension HashiCorp.terraform \
     --install-extension run-at-scale.terraform-doc-snippets \
     --install-extension GoogleCloudTools.cloudcode \
     --install-extension cody-kochmann.gcp-resource-monitor \
     --install-extension googlecloudtools.google \
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
     --install-extension eamodio.gitlens \
     --install-extension rebornix.Ruby \
     --install-extension chef-software.chef-inspec \
     --install-extension tsandall.opa \
     --install-extension playtika.vscode-cel-extension \
     --install-extension GoogleCloudTools.policy-controller
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
    "*.tfbackend": "terraform",
    "*.rb": "ruby",
    "*.rego": "rego",
    "constraint.yaml": "yaml",
    "template.yaml": "yaml",
    "policy.yaml": "yaml",
    "*.inspec.yml": "yaml",
    "*.cel": "cel"
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
  
  // Google Cloud settings
  "cloudcode.gke.performanceMode": true,
  "cloudcode.autoDependencies": true,
  "cloudcode.yaml.format.enable": true,
  "cloudcode.gcp.profileSwitching": true,
  
  // Ruby/InSpec settings
  "ruby.useLanguageServer": true,
  "ruby.format": true,
  "ruby.lint": {
    "rubocop": true
  },
  "ruby.intellisense": "rubyLocate",
  
  // OPA/Rego settings
  "rego.server.enabled": true,
  "rego.trace.server": "verbose",
  "rego.langserver.enabled": true,
  
  // Policy Controller settings
  "policyController.enabled": true,
  "policyController.validateOnSave": true,
  
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
  "[ruby]": {
    "editor.defaultFormatter": "rebornix.ruby"
  },
  "[rego]": {
    "editor.defaultFormatter": "tsandall.opa"
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
    "https://raw.githubusercontent.com/compose-spec/compose-spec/master/schema/compose-spec.json": "*docker-compose*.yml",
    "https://raw.githubusercontent.com/GoogleCloudPlatform/deploymentmanager-samples/master/templates/schema/environment.yaml": "*deployment-manager*.yaml"
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
    "eksctl",
    "gcloud",
    "gcloudsdk",
    "cloudcode",
    "googlecloud",
    "googlestorage",
    "gcsfs",
    "bigquery",
    "bigtable",
    "dataproc",
    "appengine",
    "cloudfunctions",
    "cloudsql",
    "cloudrun",
    "jsonnet",
    "inspec",
    "cinc",
    "cookstyle",
    "rubocop",
    "rego",
    "openpolicyagent",
    "cloudfoundation",
    "gatekeeper",
    "policybinding",
    "constrainttemplate",
    "customconstraint",
    "orgpolicy",
    "guardrails"
  ],
  "cSpell.enableFiletypes": [
    "terraform",
    "markdown",
    "python",
    "yaml",
    "json",
    "shellscript",
    "ruby",
    "rego",
    "cel"
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

**Before (Without Extension):**
```terraform
resource "google_storage_bucket" "logs" {
name="${var.project_name}-logs-${var.environment}"
location="US"
  
versioning {
  enabled=true
}
  
lifecycle_rule {
condition {
age=90
}
action {
type="Delete"
}
}
  
labels=var.common_labels
}
```

**After (With HashiCorp Terraform Extension):**
```terraform
resource "google_storage_bucket" "logs" {
  name     = "${var.project_name}-logs-${var.environment}"
  location = "US"
  
  versioning {
    enabled = true
  }
  
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type = "Delete"
    }
  }
  
  labels = var.common_labels
}
```

**Caught Issues:**
- Inconsistent spacing and indentation
- Missing spaces around `=` operators
- Unaligned block structures

**Benefits:**
- **Auto-completion** suggests resource types and their properties
- **Syntax highlighting** makes code more readable
- **Real-time validation** identifies errors as you type
- **Format on save** ensures consistent code style

#### Example: Module documentation with snippets

**Before (Without Terraform Doc Snippets):**
```terraform
// GCS Logs Bucket Module
// Creates a Google Cloud Storage bucket for logging

variable "project_name" {
  description = "project name"
}

variable "environment" {
  // environment name
}
```

**After (With Terraform Doc Snippets Extension):**
```terraform
/**
 * # GCS Logs Bucket Module
 *
 * This module creates a Google Cloud Storage bucket configured for logging with appropriate lifecycle policies.
 *
 * ## Usage
 * ```hcl
 * module "logs_bucket" {
 *   source       = "./modules/gcs_logs_bucket"
 *   project_name = "acme"
 *   environment  = "prod"
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

**Caught Issues:**
- Inconsistent comment styles (// vs /* */)
- Missing type declarations for variables
- Poor variable descriptions
- Lack of comprehensive documentation
- Missing usage examples

**Benefits:**
- **Doc snippets** generate standardized documentation templates
- **Auto-formatting** of comments and documentation
- **Consistent structure** for module documentation
- **Usage examples** included automatically

### Python Automation

Python is often used to automate Terraform tasks and validate infrastructure. The extensions ensure code quality:

#### Example: Terraform output validator

**Before (Without Python Extensions):**
```python
def validate_terraform_outputs(output_file, required_outputs):
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

**After (With Python + Pylint + Black Extensions):**
```python
def validate_terraform_outputs(output_file: str, required_outputs: list) -> bool:
    """
    Validates that required outputs exist in Terraform output file.
    
    Args:
        output_file (str): Path to terraform output JSON file
        required_outputs (list): List of required output names
    
    Returns:
        bool: True if all required outputs exist
    """
    try:
        with open(output_file, "r") as f:
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

**Caught Issues:**
- Missing type hints for parameters and return value
- Missing function docstring and documentation
- Inconsistent indentation and spacing
- Single vs double quotes inconsistency 
- No clear visual separation between logical blocks

**Benefits:**
- **Code linting** identifies potential bugs and style issues
- **Auto-formatting** with Black ensures consistent style
- **Type hints** improve code readability and IDE intellisense
- **Documentation help** with docstring formatting
- **Consistent spacing** between logical code blocks

### YAML Configuration

YAML is essential for CI/CD pipelines and configuration files in infrastructure:

#### Example: GitHub Actions workflow

**Before (Without YAML Extensions):**
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
   - name: Setup Google Cloud SDK
     uses: google-github-actions/setup-gcloud@v1
     with:
       service_account_key: ${{ secrets.GCP_SA_KEY }}
       project_id: ${{ secrets.GCP_PROJECT_ID }}
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

**After (With YAML Extensions):**
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
          
      - name: Setup Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
          
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

**Caught Issues:**
- Inconsistent indentation throughout the file
- Missing spacing between logical sections
- Inconsistent list item alignments
- Script indentation issues within run blocks
- Missing line breaks between major sections

**Benefits:**
- **Schema validation** ensures workflow files are correctly structured
- **Syntax highlighting** makes YAML more readable
- **Auto-formatting** ensures consistent indentation
- **YAML sorting** organizes complex configuration files
- **Visual separation** between sections improves readability

### Shell Scripting

Shell scripts automate deployment workflows and module testing:

#### Example: Module testing script

**Before (Without Shell Extensions):**
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
# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
echo "Google Cloud SDK not found. Please install gcloud first."
exit 1
fi
# Determine which modules to validate
if [ -z "$1" ]; then
# Find all modules
modules=`find . -name "main.tf" -exec dirname {} \; | sort -u`
else
# Validate specific module
modules=$1
fi
# Initialize and validate each module
for module in $modules; do
echo "================================================================"
echo "Validating module: $module"
echo "================================================================"
pushd $module > /dev/null
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

**After (With ShellCheck + Shell Format Extensions):**
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

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "Google Cloud SDK not found. Please install gcloud first."
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

**Caught Issues:**
- Missing quotes around variable references (`$module` vs `"$module"`)
- Inconsistent indentation throughout the script
- Backticks (`) used instead of recommended $() for command substitution
- Missing spacing between logical sections
- No visual separation between major script sections

**ShellCheck Specific Warnings:**
- SC2086: Double quote to prevent globbing and word splitting
- SC2046: Quote this to prevent word splitting
- SC2006: Use $(...) notation instead of legacy backticked `...`

**Benefits:**
- **ShellCheck** identifies common shell script issues and security concerns
- **Syntax highlighting** improves readability
- **Auto-formatting** ensures consistent spacing and indentation
- **Error detection** finds issues before execution
- **Best practice suggestions** for modern shell scripting

### Markdown Documentation

Quality documentation is crucial for module reusability:

#### Example: Module README.md

**Before (Without Markdown Extensions):**
```markdown
# Google Cloud Storage Secure Bucket Module
## Overview
This Terraform module creates a secure GCS bucket with encryption, versioning, and proper access controls following best practices.
## Usage
```terraform
module "secure_bucket" {
  source      = "./modules/gcs_secure_bucket"
  bucket_name = "my-secure-data"
  project_id  = "my-gcp-project"
  location    = "US"
  environment = "production"
  
  # Optional configurations
  versioning_enabled = true
  
  labels = {
    department = "Finance"
    project    = "Data Warehouse"
  }
}
```
## Inputs
| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
|bucket_name|Name of the GCS bucket|`string`|n/a|yes|
|project_id|Google Cloud Project ID|`string`|n/a|yes|
|location|Location for the bucket|`string`|`"US"`|no|
|environment|Deployment environment|`string`|n/a|yes|
|versioning_enabled|Enable versioning for the bucket|`bool`|`true`|no|
|labels|Resource labels|`map(string)`|`{}`|no|
## Outputs
| Name | Description |
|------|-------------|
|bucket_name|The name of the bucket|
|bucket_url|The URL of the bucket|
|bucket_self_link|The self_link of the bucket|
```

**After (With Markdown All in One + markdownlint Extensions):**
```markdown
# Google Cloud Storage Secure Bucket Module

## Overview

This Terraform module creates a secure GCS bucket with encryption, versioning, and proper access controls following best practices.

## Usage

```terraform
module "secure_bucket" {
  source      = "./modules/gcs_secure_bucket"
  bucket_name = "my-secure-data"
  project_id  = "my-gcp-project"
  location    = "US"
  environment = "production"
  
  # Optional configurations
  versioning_enabled = true
  
  labels = {
    department = "Finance"
    project    = "Data Warehouse"
  }
}
```

## Inputs

| Name | Description | Type | Default | Required |
|------|-------------|------|---------|:--------:|
| bucket_name | Name of the GCS bucket | `string` | n/a | yes |
| project_id | Google Cloud Project ID | `string` | n/a | yes |
| location | Location for the bucket | `string` | `"US"` | no |
| environment | Deployment environment | `string` | n/a | yes |
| versioning_enabled | Enable versioning for the bucket | `bool` | `true` | no |
| labels | Resource labels | `map(string)` | `{}` | no |

## Outputs

| Name | Description |
|------|-------------|
| bucket_name | The name of the bucket |
| bucket_url | The URL of the bucket |
| bucket_self_link | The self_link of the bucket |
```

**Caught Issues:**
- Missing blank lines after headings (MD022)
- Missing spaces in table cells (MD055)
- Inconsistent line breaks between sections
- Missing spacing around table content
- No blank line before code blocks (MD031)

**Benefits:**
- **Table formatting** automatically aligns table columns
- **TOC generation** creates navigation for long documents
- **Link validation** ensures all references work
- **Preview** shows final rendered output
- **Linting rules** enforce consistent style and readability
- **Automatic list formatting** for ordered and unordered lists

### Spell Checking

Consistent spelling improves professionalism in code and documentation:

#### Example: With and without spell checking

**Before:**
```terraform
resource "google_project_iam_polcy" "storage_acess" {
  project     = var.project_id
  role        = "storage-bucket-acess-role"
  description = "Policy that grants permisions to the logging buckt"
  
  members = [
    "serviceAccount:${google_service_account.logging_service_acount.email}",
  ]
}
```

**After (with spell checking):**
```terraform
resource "google_project_iam_policy" "storage_access" {
  project     = var.project_id
  role        = "storage-bucket-access-role"
  description = "Policy that grants permissions to the logging bucket"
  
  members = [
    "serviceAccount:${google_service_account.logging_service_account.email}",
  ]
}
```

**Benefits:**
- **Highlights typos** in resource names and descriptions
- **Technical terminology** is recognized with custom dictionary
- **Reduces confusion** in shared code
- **Improves searchability** of code and documentation

### Google Cloud Development

The Google Cloud extensions enhance your workflow when working with GCP resources:

#### Example: Cloud Run service with Cloud Code

**Before (Without Cloud Code Extension):**
```terraform
resource "google_cloud_run_service" "default" {
  name = "api-service"
  location = "us-central1"
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/api-service:latest"
        resources {
          limits = {
            cpu = "1000m"
            memory = "512Mi"
          }
        }
        env {
          name = "ENVIRONMENT"
          value = var.environment
        }
      }
    }
  }
  traffic {
    percent = 100
    latest_revision = true
  }
}
```

**After (With Cloud Code Extension):**
```terraform
resource "google_cloud_run_service" "default" {
  name     = "api-service"
  location = "us-central1"
  
  template {
    spec {
      containers {
        image = "gcr.io/${var.project_id}/api-service:latest"
        
        resources {
          limits = {
            cpu    = "1000m"
            memory = "512Mi"
          }
        }
        
        env {
          name  = "ENVIRONMENT"
          value = var.environment
        }
      }
    }
  }
  
  traffic {
    percent         = 100
    latest_revision = true
  }
}
```

**Caught Issues:**
- Formatting inconsistencies (spacing, alignment)
- Missing logical section breaks between blocks
- Missing validation for GCP-specific resource properties
- Cloud Code would also highlight if region values were invalid
- Missing alignment of `=` signs for readability

**Benefits:**
- **Cloud Code integration** provides GCP-specific IntelliSense
- **Project explorer** for GCP resources
- **Deployment assistance** for Cloud Run, GKE, and App Engine
- **Local development emulators** for GCP services
- **GCP-specific property validation** (e.g., valid regions, machine types)

#### Example: Python with Google Cloud client libraries

**Before (Without Cloud Code + Python Extensions):**
```python
from google.cloud import storage

def list_buckets(project_id):
    storage_client = storage.Client(project=project_id)
    buckets = storage_client.list_buckets()
    
    bucket_names = []
    for bucket in buckets:
        bucket_names.append(bucket.name)
        
    return bucket_names
```

**After (With Cloud Code + Python Extensions):**
```python
from google.cloud import storage
from typing import List

def list_buckets(project_id: str) -> List[str]:
    """
    List all storage buckets in a given project.
    
    Args:
        project_id (str): Google Cloud Project ID
        
    Returns:
        List[str]: List of bucket names
    """
    storage_client = storage.Client(project=project_id)
    buckets = storage_client.list_buckets()
    
    bucket_names = []
    for bucket in buckets:
        bucket_names.append(bucket.name)
        
    return bucket_names
```

**Caught Issues:**
- Missing type hints for parameters and return values
- Missing function docstring
- Missing import for typing module
- No documentation for method purpose or parameters

**Benefits:**
- **Auto-imports** for Google Cloud libraries
- **Method suggestions** for Google Cloud client libraries
- **Documentation on hover** for Google Cloud methods
- **Authentication help** for local development
- **Type hinting** for GCP-specific classes and methods

ored for GCP YAML files
- **Error detection** for invalid GCP configurations

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

5. **Google Cloud Integration**:
   - Cloud Code explorer for viewing GCP resources
   - Easy authentication switching between projects
   - Emulators for local development and testing

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

6. **Google Cloud authentication issues**
   - Run `gcloud auth application-default login` in your terminal
   - Check that GOOGLE_APPLICATION_CREDENTIALS environment variable is set correctly
   - Use Cloud Code authentication switcher to change between accounts

7. **Policy validation errors**
   - Ensure OPA server is running for Rego validation
   - Check CEL syntax with the CEL playground
   - Validate Gatekeeper constraints against template
   - Run InSpec syntax check with `inspec check`

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

6. **Use Cloud Code features**
   - Leverage the GCP emulators for local testing
   - Use the Cloud Explorer to navigate resources
   - Set up multiple GCP profiles for different projects

7. **Contribute to our extensions list**
   - If you find a useful extension, suggest it to the team for inclusion in our standard setup
