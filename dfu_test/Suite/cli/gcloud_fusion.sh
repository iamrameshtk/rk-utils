#!/bin/bash

###############################################################################
# Google Cloud Data Fusion CLI Test Script
# Description: Tests all available gcloud beta data-fusion CLI commands
# Author: Cloud Data Fusion Test Automation
# Version: 1.4
# 
# IMPORTANT: This script is designed for users with custom role permissions 
# that include only read operations. All update/modify operations are 
# expected to fail due to insufficient permissions.
#
# Compatible with: Linux, macOS, BSD
# 
# Optimizations:
# - Uses --async flag for all long-running operations to improve test speed
# - Permission checks happen immediately, even with --async
###############################################################################

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output (cross-platform)
print_info() {
    printf "${BLUE}[INFO]${NC} %s\n" "$1"
}

print_success() {
    printf "${GREEN}[SUCCESS]${NC} %s\n" "$1"
}

print_error() {
    printf "${RED}[ERROR]${NC} %s\n" "$1"
}

print_warning() {
    printf "${YELLOW}[WARNING]${NC} %s\n" "$1"
}

# Function to calculate elapsed time (cross-platform)
calculate_elapsed_time() {
    local start=$1
    local end=$2
    local elapsed=$((end - start))
    local hours=$((elapsed / 3600))
    local minutes=$(((elapsed % 3600) / 60))
    local seconds=$((elapsed % 60))
    printf '%02d:%02d:%02d' $hours $minutes $seconds
}

# Function to display usage
usage() {
    cat << EOF
Usage: $0 -p PROJECT_ID -l LOCATION -i INSTANCE_NAME [-n NAMESPACE] [-h]

This script tests all available gcloud beta data-fusion CLI commands.

Parameters:
    -p PROJECT_ID       GCP Project ID (required)
    -l LOCATION         Region/Location (required, e.g., us-central1)
    -i INSTANCE_NAME    Data Fusion instance name (required)
    -n NAMESPACE        Namespace (optional, default: default)
    -h                  Display this help message

Example:
    $0 -p my-project -l us-central1 -i my-instance

Output:
    - Test results in CSV format: data_fusion_test_results_<timestamp>.csv
    - Detailed log file: data_fusion_test_<timestamp>.log
EOF
    exit 1
}

# Parse command line arguments
while getopts "p:l:i:n:h" opt; do
    case $opt in
        p)
            PROJECT_ID="$OPTARG"
            ;;
        l)
            LOCATION="$OPTARG"
            ;;
        i)
            INSTANCE_NAME="$OPTARG"
            ;;
        n)
            NAMESPACE="$OPTARG"
            ;;
        h)
            usage
            ;;
        \?)
            echo "Invalid option: -$OPTARG" >&2
            usage
            ;;
    esac
done

# Check required parameters
if [ -z "$PROJECT_ID" ] || [ -z "$LOCATION" ] || [ -z "$INSTANCE_NAME" ]; then
    print_error "Missing required parameters"
    usage
fi

# Set default namespace if not provided
NAMESPACE=${NAMESPACE:-default}

# Create output directory and files
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="data_fusion_test_results_${TIMESTAMP}"
mkdir -p "$OUTPUT_DIR"
LOG_FILE="$OUTPUT_DIR/data_fusion_test_${TIMESTAMP}.log"
CSV_FILE="$OUTPUT_DIR/data_fusion_test_results_${TIMESTAMP}.csv"
TEST_SUMMARY="$OUTPUT_DIR/test_summary_${TIMESTAMP}.txt"

# Initialize CSV file with headers
echo "Test Case ID,Test Case Name,Command,Status,Execution Time (seconds),Output,Error Message,Timestamp" > "$CSV_FILE"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to execute command and capture results
execute_test() {
    local test_id=$1
    local test_name=$2
    local command=$3
    local expected_failure=${4:-false}
    
    log "Executing Test Case $test_id: $test_name"
    log "Command: $command"
    
    # Execute command and capture output, error, and timing
    local start_time=$(date +%s)
    local output
    local error_msg
    local exit_code
    
    # Execute command and capture both stdout and stderr
    if output=$(eval "$command" 2>&1); then
        exit_code=0
    else
        exit_code=$?
    fi
    
    local end_time=$(date +%s)
    local execution_time=$((end_time - start_time))
    
    # Determine test status
    local status
    if [ $exit_code -eq 0 ]; then
        if [ "$expected_failure" = "true" ]; then
            status="UNEXPECTED_PASS"
        else
            status="PASS"
        fi
        error_msg=""
    else
        if [ "$expected_failure" = "true" ]; then
            status="EXPECTED_FAIL"
        else
            status="FAIL"
        fi
        error_msg="$output"
        output=""
    fi
    
    # Clean output for CSV (remove newlines and commas)
    output=$(echo "$output" | tr '\n' ' ' | tr ',' ';')
    error_msg=$(echo "$error_msg" | tr '\n' ' ' | tr ',' ';')
    
    # Write to CSV
    echo "$test_id,$test_name,$command,$status,$execution_time,\"$output\",\"$error_msg\",$(date '+%Y-%m-%d %H:%M:%S')" >> "$CSV_FILE"
    
    # Log result
    if [ "$status" = "PASS" ]; then
        print_success "Test $test_id passed in ${execution_time}s"
    elif [ "$status" = "EXPECTED_FAIL" ]; then
        print_warning "Test $test_id failed as expected in ${execution_time}s"
    else
        print_error "Test $test_id failed in ${execution_time}s"
    fi
    
    echo "---" >> "$LOG_FILE"
}

# Start testing
start_time=$(date +%s)
log "=== Google Cloud Data Fusion CLI Test Suite ==="
log "Project: $PROJECT_ID"
log "Location: $LOCATION"
log "Instance: $INSTANCE_NAME"
log "Namespace: $NAMESPACE"
log "Test Started: $(date)"
echo

# Test Case 1: Check if gcloud is installed and authenticated
execute_test "TC001" "Check gcloud installation" "gcloud version"

# Test Case 2: Set project
execute_test "TC002" "Set project" "gcloud config set project $PROJECT_ID"

# Test Case 3: Check Data Fusion API status
execute_test "TC003" "Check Data Fusion API" "gcloud services list --filter='name:datafusion.googleapis.com' --format='value(name)'"

# Test Case 4: List all Data Fusion instances
execute_test "TC004" "List instances" "gcloud beta data-fusion instances list --location=$LOCATION --format=json"

# Test Case 5: Describe specific instance
execute_test "TC005" "Describe instance" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format=json"

# Test Case 6: Get instance IAM policy
execute_test "TC006" "Get IAM policy" "gcloud beta data-fusion get-iam-policy $INSTANCE_NAME --location=$LOCATION"

# Test Case 7: List operations
execute_test "TC007" "List operations" "gcloud beta data-fusion operations list --location=$LOCATION --format=json"

# Test Case 8: Update instance (add label) - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
TEST_LABEL_KEY="test-run"
TEST_LABEL_VALUE="automated-${TIMESTAMP}"
execute_test "TC008" "Update instance labels" "gcloud beta data-fusion instances update $INSTANCE_NAME --location=$LOCATION --update-labels=${TEST_LABEL_KEY}=${TEST_LABEL_VALUE} --async" "true"

# Test Case 9: Update instance options - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
execute_test "TC009" "Update instance options" "gcloud beta data-fusion instances update $INSTANCE_NAME --location=$LOCATION --options=system.profile.properties.dataproc.preferExternalIP=true --async" "true"

# Test Case 10: Restart instance - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
execute_test "TC010" "Restart instance" "gcloud beta data-fusion instances restart $INSTANCE_NAME --location=$LOCATION --async" "true"

# Test Case 11: Skip wait since restart won't happen with custom role permissions
log "Skipping wait for restart operation (custom role permissions don't allow restart)"

# Test Case 12: Enable stack driver logging - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
execute_test "TC012" "Enable Stackdriver logging" "gcloud beta data-fusion instances update $INSTANCE_NAME --location=$LOCATION --enable_stackdriver_logging --async" "true"

# Test Case 13: Enable stack driver monitoring - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
execute_test "TC013" "Enable Stackdriver monitoring" "gcloud beta data-fusion instances update $INSTANCE_NAME --location=$LOCATION --enable_stackdriver_monitoring --async" "true"

# Test Case 14: Update instance description - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
execute_test "TC014" "Update instance description" "gcloud beta data-fusion instances update $INSTANCE_NAME --location=$LOCATION --description='Updated by automated test at ${TIMESTAMP}' --async" "true"

# Test Case 15: Add IAM policy binding - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
TEST_USER="user:test-automation@example.com"
execute_test "TC015" "Add IAM policy binding" "gcloud beta data-fusion add-iam-policy-binding $INSTANCE_NAME --location=$LOCATION --member=$TEST_USER --role=roles/datafusion.viewer" "true"

# Test Case 16: Remove IAM policy binding - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
execute_test "TC016" "Remove IAM policy binding" "gcloud beta data-fusion remove-iam-policy-binding $INSTANCE_NAME --location=$LOCATION --member=$TEST_USER --role=roles/datafusion.viewer" "true"

# Test Case 17: Get API endpoint
execute_test "TC017" "Get API endpoint" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(apiEndpoint)'"

# Test Case 18: Get service endpoint
execute_test "TC018" "Get service endpoint" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(serviceEndpoint)'"

# Test Case 19: Get instance state
execute_test "TC019" "Get instance state" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(state)'"

# Test Case 20: Get instance version
execute_test "TC020" "Get instance version" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(version)'"

# Test Case 21: List available versions
execute_test "TC021" "List available versions" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(availableVersion[])'"

# Test Case 22: Get instance type
execute_test "TC022" "Get instance type" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(type)'"

# Test Case 23: Get private instance status
execute_test "TC023" "Get private instance status" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(privateInstance)'"

# Test Case 24: Get network config
execute_test "TC024" "Get network config" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(networkConfig)'"

# Test Case 25: Update instance with zone - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
execute_test "TC025" "Update instance zone" "gcloud beta data-fusion instances update $INSTANCE_NAME --location=$LOCATION --zone=${LOCATION}-a --async" "true"

# Test Case 26: Clear labels - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
execute_test "TC026" "Clear instance labels" "gcloud beta data-fusion instances update $INSTANCE_NAME --location=$LOCATION --clear-labels --async" "true"

# Test Case 27: List operations with filter
execute_test "TC027" "List operations with filter" "gcloud beta data-fusion operations list --location=$LOCATION --filter='name:$INSTANCE_NAME' --format=json"

# Test Case 28: Describe latest operation
execute_test "TC028" "Describe latest operation" "gcloud beta data-fusion operations list --location=$LOCATION --limit=1 --format='value(name)' | xargs -I {} gcloud beta data-fusion operations describe {} --location=$LOCATION" "true"

# Test Case 29: Set IAM policy from file - EXPECTED TO FAIL WITH CUSTOM ROLE PERMISSIONS
# Create a temporary IAM policy file
IAM_POLICY_FILE="$OUTPUT_DIR/test_iam_policy.json"
cat > "$IAM_POLICY_FILE" << EOF
{
  "bindings": [
    {
      "role": "roles/datafusion.viewer",
      "members": [
        "user:viewer@example.com"
      ]
    }
  ]
}
EOF

execute_test "TC029" "Set IAM policy from file" "gcloud beta data-fusion set-iam-policy $INSTANCE_NAME --location=$LOCATION $IAM_POLICY_FILE" "true"

# Test Case 30: Check instance creation time
execute_test "TC030" "Get instance creation time" "gcloud beta data-fusion instances describe $INSTANCE_NAME --location=$LOCATION --format='value(createTime)'"

# Generate test summary
log "Generating test summary..."

# Count test results
TOTAL_TESTS=$(grep -c "^TC" "$CSV_FILE")
PASSED_TESTS=$(grep -c ",PASS," "$CSV_FILE")
FAILED_TESTS=$(grep -c ",FAIL," "$CSV_FILE")
EXPECTED_FAILURES=$(grep -c ",EXPECTED_FAIL," "$CSV_FILE")
UNEXPECTED_PASSES=$(grep -c ",UNEXPECTED_PASS," "$CSV_FILE")

# Calculate success rate (PASS + EXPECTED_FAIL)
if [ $TOTAL_TESTS -gt 0 ]; then
    SUCCESS_RATE=$(awk "BEGIN {printf \"%.2f\", (($PASSED_TESTS + $EXPECTED_FAILURES)/$TOTAL_TESTS)*100}")
else
    SUCCESS_RATE=0
fi

# Write test summary
cat > "$TEST_SUMMARY" << EOF
================================================================================
                    Google Cloud Data Fusion CLI Test Summary
================================================================================
Test Execution Date: $(date)
Project ID: $PROJECT_ID
Location: $LOCATION
Instance Name: $INSTANCE_NAME
Namespace: $NAMESPACE
User Permissions: Custom Role (Read-Only)

Test Results:
-------------
Total Tests Executed: $TOTAL_TESTS
Passed (Read Operations): $PASSED_TESTS
Failed (Unexpected): $FAILED_TESTS
Expected Failures (Write Operations): $EXPECTED_FAILURES
Unexpected Passes: $UNEXPECTED_PASSES
Success Rate: ${SUCCESS_RATE}%

Note: Success rate includes both PASS and EXPECTED_FAIL results.
Write operations are expected to fail with custom role read-only permissions.

Output Files:
-------------
CSV Results: $CSV_FILE
Detailed Log: $LOG_FILE
Test Summary: $TEST_SUMMARY

Test Execution Time: $(calculate_elapsed_time $start_time $(date +%s))
================================================================================
EOF

# Display summary
cat "$TEST_SUMMARY"

# Create HTML report
HTML_REPORT="$OUTPUT_DIR/test_report_${TIMESTAMP}.html"
cat > "$HTML_REPORT" << EOF
<!DOCTYPE html>
<html>
<head>
    <title>Data Fusion CLI Test Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        h1 { color: #1a73e8; }
        table { border-collapse: collapse; width: 100%; margin-top: 20px; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
        .pass { background-color: #d4edda; }
        .fail { background-color: #f8d7da; }
        .expected-fail { background-color: #fff3cd; }
        .summary { background-color: #e7f3ff; padding: 15px; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <h1>Google Cloud Data Fusion CLI Test Report</h1>
    <div class="summary">
        <h2>Test Summary</h2>
        <p><strong>Project:</strong> $PROJECT_ID</p>
        <p><strong>Location:</strong> $LOCATION</p>
        <p><strong>Instance:</strong> $INSTANCE_NAME</p>
        <p><strong>User Permissions:</strong> Custom Role (Read-Only)</p>
        <p><strong>Total Tests:</strong> $TOTAL_TESTS</p>
        <p><strong>Passed (Read Operations):</strong> $PASSED_TESTS</p>
        <p><strong>Failed (Unexpected):</strong> $FAILED_TESTS</p>
        <p><strong>Expected Failures (Write Operations):</strong> $EXPECTED_FAILURES</p>
        <p><strong>Success Rate:</strong> ${SUCCESS_RATE}%</p>
        <p><em>Note: Write operations are expected to fail with custom role read-only permissions.</em></p>
    </div>
    <h2>Test Results</h2>
    <table>
        <tr>
            <th>Test ID</th>
            <th>Test Name</th>
            <th>Command</th>
            <th>Status</th>
            <th>Execution Time (s)</th>
            <th>Timestamp</th>
        </tr>
EOF

# Add test results to HTML
tail -n +2 "$CSV_FILE" | while IFS=',' read -r test_id test_name command status exec_time output error timestamp; do
    class=""
    case $status in
        "PASS") class="pass" ;;
        "FAIL") class="fail" ;;
        "EXPECTED_FAIL") class="expected-fail" ;;
    esac
    echo "        <tr class=\"$class\">" >> "$HTML_REPORT"
    echo "            <td>$test_id</td>" >> "$HTML_REPORT"
    echo "            <td>$test_name</td>" >> "$HTML_REPORT"
    echo "            <td><code>$command</code></td>" >> "$HTML_REPORT"
    echo "            <td>$status</td>" >> "$HTML_REPORT"
    echo "            <td>$exec_time</td>" >> "$HTML_REPORT"
    echo "            <td>$timestamp</td>" >> "$HTML_REPORT"
    echo "        </tr>" >> "$HTML_REPORT"
done

echo "    </table>" >> "$HTML_REPORT"
echo "</body>" >> "$HTML_REPORT"
echo "</html>" >> "$HTML_REPORT"

print_info "Test execution completed!"
print_info "Results saved to: $OUTPUT_DIR"
print_info "CSV file: $CSV_FILE"
print_info "HTML report: $HTML_REPORT"
print_info "Log file: $LOG_FILE"
print_info "Summary: $TEST_SUMMARY"
