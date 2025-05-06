# Basic usage - import a profile using the profile name and project ID
export GOOGLE_ACCESS_TOKEN="ya29.a0AWY_..." # Should be set by Harness secret
python import_compute_profile.py --profile-name dataproc-ephemeral --project-id my-gcp-project

# Specify a different configuration directory
python import_compute_profile.py --profile-name dataproc-ephemeral --project-id my-gcp-project --config-dir /path/to/compute_profile

# Specify all parameters explicitly
python import_compute_profile.py \
  --profile-name dataproc-ephemeral \
  --project-id my-gcp-project \
  --config-dir ./compute_profile \
  --datafusion-instance my-datafusion \
  --datafusion-location us-central1 \
  --namespace default

# Enable verbose logging
python import_compute_profile.py --profile-name dataproc-ephemeral --project-id my-gcp-project --verbose

# Using with Harness (example of how it would be used in a Harness pipeline)
# In Harness, the GOOGLE_ACCESS_TOKEN would be set from a secret
# <+secrets.getValue("GOOGLE_ACCESS_TOKEN")>
python import_compute_profile.py \
  --profile-name <+pipeline.variables.profile_name> \
  --project-id <+pipeline.variables.project_id> \
  --datafusion-instance <+pipeline.variables.datafusion_instance>

# Multiple profiles can be imported by running the script multiple times
python import_compute_profile.py --profile-name dataproc-ephemeral-small --project-id my-gcp-project
python import_compute_profile.py --profile-name dataproc-ephemeral-large --project-id my-gcp-project
