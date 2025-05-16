# Data Fusion Compute Profile Importer

A Python utility for importing Dataproc compute profile configurations to Google Cloud Data Fusion instances.

## Overview

This script allows you to import one or more Dataproc compute profile configurations into a Cloud Data Fusion instance using the REST API. It supports both single profile imports and bulk imports of multiple profiles at once.

## Features

- Import a single profile by name
- Import multiple profiles from a directory
- Auto-detection of Data Fusion instances
- Authentication via Harness secrets
- Comprehensive error handling and logging
- Flexible profile discovery
- SSL verification fallback (automatically disables SSL verification if SSL errors occur)

## Prerequisites

- Python 3.6+
- `requests` library (`pip install requests`)
- A Google Cloud project with Cloud Data Fusion enabled
- A valid Google Cloud access token (via Harness secrets or other methods)

## Installation

Clone this repository or download the script:

```bash
git clone https://github.com/your-org/datafusion-profile-importer.git
cd datafusion-profile-importer
```

## Authentication

The script requires a Google Cloud access token for authentication. It looks for this token in the `GOOGLE_ACCESS_TOKEN` environment variable. This can be set directly or, preferably, provided via Harness secrets:

```bash
export GOOGLE_ACCESS_TOKEN="ya29.a0AWY_..."
```

In a Harness pipeline, you would typically use:

```
<+secrets.getValue("GOOGLE_ACCESS_TOKEN")>
```

## Usage

### Basic Usage

Import a single profile:

```bash
python import_compute_profile.py --profile-name dataproc-ephemeral --project-id my-gcp-project
```

Import multiple profiles:

```bash
python import_compute_profile.py --profile-dir profiles --project-id my-gcp-project
```

### Command Line Arguments

| Argument | Description | Required | Default |
|----------|-------------|----------|---------|
| `--profile-name` | Name of a single Dataproc profile to import | Either this or `--profile-dir` | - |
| `--profile-dir` | Directory containing multiple profile configurations to import | Either this or `--profile-name` | - |
| `--project-id` | GCP Project ID | Yes | - |
| `--config-dir` | Directory containing profile configuration files | No | `./compute_profile` |
| `--datafusion-instance` | Data Fusion instance name | No | Auto-detected |
| `--datafusion-location` | Data Fusion instance location | No | `us-central1` |
| `--namespace` | Data Fusion namespace | No | `default` |
| `--verbose` | Enable verbose logging | No | `False` |

### Examples

Import a single profile with all parameters specified:

```bash
python import_compute_profile.py \
  --profile-name dataproc-ephemeral \
  --project-id my-gcp-project \
  --config-dir ./compute_profile \
  --datafusion-instance my-datafusion \
  --datafusion-location us-central1 \
  --namespace default
```

Import multiple profiles with verbose logging:

```bash
python import_compute_profile.py \
  --profile-dir profiles \
  --project-id my-gcp-project \
  --verbose
```

## Directory Structure

### Understanding `config-dir` and `profile-dir`

The script uses two directory parameters that work together:

- `config-dir`: The base directory containing all configuration files (default: `./compute_profile`)
- `profile-dir`: A subdirectory of `config-dir` (unless an absolute path is provided) containing multiple profile configurations

### Profile Configuration Discovery

#### Single Profile Mode (using `--profile-name`)

When a single profile name is specified, the script looks for:

1. `{config-dir}/{profile-name}.json`
2. `{config-dir}/{profile-name}/config.json`
3. `{config-dir}/config.json`
4. `{config-dir}/profile.json`

#### Multiple Profile Mode (using `--profile-dir`)

When a directory of profiles is specified, the script:

1. Scans for all `.json` files in `{config-dir}/{profile-dir}/`
2. Scans for subdirectories with `config.json` files inside

### How Profile Names Are Determined

The script determines profile names using these rules in order:

1. If the JSON configuration contains a `name` field, use that as the profile name
2. If the file is named `config.json`, use its parent directory name as the profile name
3. Otherwise, use the filename (without `.json` extension) as the profile name

### Example Directory Structures

**Single Profile Example:**
```
compute_profile/                 (config-dir)
├── dataproc-ephemeral.json      (direct file, named after profile)
```

**Single Profile in Subdirectory:**
```
compute_profile/                 (config-dir)
├── dataproc-ephemeral/          (subdirectory named after profile)
    └── config.json              (configuration in config.json)
```

**Multiple Profiles:**
```
compute_profile/                 (config-dir)
├── profiles/                    (profile-dir)
    ├── small.json               (profile named "small")
    ├── medium.json              (profile named "medium")
    ├── large/                   (subdirectory for "large" profile)
    │   └── config.json          (config for "large" profile)
    └── custom-profile.json      (profile with custom name in JSON)
```

## Profile Configuration Format

A Dataproc compute profile configuration must be in JSON format and include at least:

```json
{
  "name": "dataproc-ephemeral",
  "provisioner": {
    "name": "gcp-dataproc",
    "properties": [
      {"name": "projectId", "value": "my-gcp-project"},
      {"name": "region", "value": "us-central1"},
      {"name": "zone", "value": "us-central1-a"},
      {"name": "masterNumNodes", "value": "1"},
      {"name": "workerNumNodes", "value": "2"},
      {"name": "masterMachineType", "value": "n1-standard-4"},
      {"name": "workerMachineType", "value": "n1-standard-4"},
      {"name": "idleTTL", "value": "3600"}
    ]
  }
}
```

## Integration with Harness

This script is designed to be used in Harness CI/CD pipelines. Example usage in a Harness pipeline:

```bash
# Set environment variables from Harness secrets
export GOOGLE_ACCESS_TOKEN="<+secrets.getValue('GOOGLE_ACCESS_TOKEN')>"

# Run the script with pipeline variables
python import_compute_profile.py \
  --profile-dir <+pipeline.variables.profile_dir> \
  --project-id <+pipeline.variables.project_id> \
  --datafusion-instance <+pipeline.variables.datafusion_instance>
```

## Error Handling

- If the script encounters errors with specific profiles in multi-profile mode, it will continue processing other profiles
- A summary report is provided at the end showing success and failure counts
- Detailed error messages are logged for troubleshooting
- The script returns exit code 0 if all profiles succeed, 1 if any failures occur

## Troubleshooting

If you encounter issues:

1. Enable verbose logging with `--verbose`
2. Check that your access token is valid and has the necessary permissions
3. Verify that the Data Fusion instance exists and is running
4. Ensure your profile configurations are valid JSON and follow the required format

## License

[Your License Here]

## Contributing

[Your Contributing Guidelines Here]
