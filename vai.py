#!/usr/bin/env python3
"""
Vertex AI Model Registry - Model Registration Script
Uses the google-cloud-aiplatform Python SDK.
All configuration is loaded from a .env file.

Install dependencies:
    pip install google-cloud-aiplatform python-dotenv

Usage:
    1. Copy .env.example to .env and fill in your values.
    2. python register_vertex_model.py
"""

import json
import logging
import os
import re
import sys

from dotenv import load_dotenv
from google.cloud import aiplatform
from google.cloud.aiplatform import Model
from google.oauth2.credentials import Credentials

# Load .env file before anything else
load_dotenv(dotenv_path=".env")

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


# ─────────────────────────────────────────────
# Env variable helpers  (mirrors train script)
# ─────────────────────────────────────────────

def get_env_value(key: str, required: bool = True, default: str = None) -> str:
    """Read an env variable; raise on missing required ones, warn on missing optional ones."""
    value = os.getenv(key, "").strip()
    if not value and required:
        logging.error(f"Environment variable '{key}' is required but empty.")
        raise ValueError(f"Environment variable '{key}' is required but empty.")
    if not value and not required:
        logging.warning(
            f"Optional environment variable '{key}' is not set. "
            f"Using default value '{default}'."
        )
        value = default if default is not None else ""
    logging.info(f"Retrieved '{key}': '{value if value else '[empty]'}'")
    return value


def get_env_list(key: str, required: bool = False) -> list[str]:
    """
    Read a comma-separated env variable into a list.
    e.g.  KEY=a=1,b=2  →  ['a=1', 'b=2']
          KEY=8080,8081 →  ['8080', '8081']
    Returns [] if not set (when not required).
    """
    raw = os.getenv(key, "").strip()
    if not raw and required:
        raise ValueError(f"Environment variable '{key}' is required but empty.")
    return [item.strip() for item in raw.split(",") if item.strip()] if raw else []


def get_env_bool(key: str, default: bool = False) -> bool:
    """Read a boolean env variable (true/1/yes → True)."""
    return os.getenv(key, str(default)).strip().lower() in ("true", "1", "yes")


# ─────────────────────────────────────────────
# Auth
# ─────────────────────────────────────────────

def get_credentials() -> Credentials:
    """Build google-auth Credentials from the CLOUD_TOKEN env variable."""
    token = get_env_value("CLOUD_TOKEN")
    return Credentials(token=token)


# ─────────────────────────────────────────────
# Config  (all sourced from .env)
# ─────────────────────────────────────────────

class Config:
    """Single place that reads and validates every env variable used by this script."""

    def __init__(self):
        # ── Required ──────────────────────────
        self.project         = get_env_value("PROJECT")
        self.location        = get_env_value("LOCATION")
        self.display_name    = get_env_value("DISPLAY_NAME")
        self.artifact_uri    = get_env_value("ARTIFACT_URI")
        self.container_image = get_env_value("CONTAINER_IMAGE")

        # ── Optional metadata ─────────────────
        self.description         = get_env_value("DESCRIPTION",         required=False, default=None) or None
        self.version_description = get_env_value("VERSION_DESCRIPTION", required=False, default=None) or None
        self.model_id            = get_env_value("MODEL_ID",            required=False, default=None) or None

        # Labels: LABELS=env=prod,team=ml
        raw_labels = get_env_list("LABELS", required=False)
        self.labels = dict(pair.split("=", 1) for pair in raw_labels) if raw_labels else None

        # ── Container options ─────────────────
        self.predict_route  = get_env_value("PREDICT_ROUTE",  required=False, default=None) or None
        self.health_route   = get_env_value("HEALTH_ROUTE",   required=False, default=None) or None

        # CONTAINER_PORTS=8080,8081
        raw_ports = get_env_list("CONTAINER_PORTS", required=False)
        self.container_ports = [int(p) for p in raw_ports] if raw_ports else None

        # CONTAINER_ENV_VARS=AIP_HTTP_PORT=8080,MODEL_ENV=production
        raw_env_vars = get_env_list("CONTAINER_ENV_VARS", required=False)
        self.env_vars = (
            dict(pair.split("=", 1) for pair in raw_env_vars) if raw_env_vars else None
        )

        # ── Behaviour flags ───────────────────
        self.dry_run = get_env_bool("DRY_RUN",  default=False)
        self.no_wait = get_env_bool("NO_WAIT",  default=False)


# ─────────────────────────────────────────────
# Version-alias resolution
# ─────────────────────────────────────────────

def _version_number(alias: str) -> int | None:
    """Extract trailing integer from strings like 'v3', 'version-3', '3'."""
    m = re.search(r"(\d+)$", alias)
    return int(m.group(1)) if m else None


def next_version_alias(existing_aliases: list[str]) -> str:
    """
    Inspect existing aliases and return the next 'vN' alias.
    e.g. ['v1', 'v2', 'default'] → 'v3'.  No aliases found → 'v1'.
    """
    numbers = [_version_number(a) for a in existing_aliases if _version_number(a) is not None]
    return f"v{max(numbers) + 1}" if numbers else "v1"


# ─────────────────────────────────────────────
# Model lookup via SDK
# ─────────────────────────────────────────────

def find_existing_models(display_name: str) -> list[Model]:
    """Return all Model resources that match the given display name."""
    return Model.list(filter=f'display_name="{display_name}"')


def collect_all_aliases(models: list[Model]) -> list[str]:
    """Gather versionAliases across all returned model versions."""
    all_aliases: list[str] = []
    for m in models:
        refreshed = Model(model_name=m.resource_name)
        aliases = list(getattr(refreshed._gca_resource, "version_aliases", []))
        logging.info(f"  {m.resource_name}  →  aliases: {aliases}")
        all_aliases.extend(aliases)
    return all_aliases


# ─────────────────────────────────────────────
# Registration
# ─────────────────────────────────────────────

def register_model(cfg: Config, version_alias: str, parent_model: Model | None) -> Model:
    """Upload the model (or a new version) using the aiplatform SDK."""

    if cfg.dry_run:
        payload = {
            "display_name":                        cfg.display_name,
            "artifact_uri":                        cfg.artifact_uri,
            "serving_container_image_uri":         cfg.container_image,
            "serving_container_predict_route":     cfg.predict_route,
            "serving_container_health_route":      cfg.health_route,
            "serving_container_ports":             cfg.container_ports,
            "serving_container_environment_variables": cfg.env_vars,
            "description":                         cfg.description,
            "labels":                              cfg.labels,
            "version_aliases":                     [version_alias],
            "version_description":                 cfg.version_description,
            "parent_model":  parent_model.resource_name if parent_model else None,
            "model_id":      cfg.model_id if not parent_model else None,
        }
        print(f"\nDRY RUN — would call Model.upload() with:\n{json.dumps(payload, indent=2, default=str)}")
        sys.exit(0)

    model = Model.upload(
        display_name=cfg.display_name,
        artifact_uri=cfg.artifact_uri,
        # Container
        serving_container_image_uri=cfg.container_image,
        serving_container_predict_route=cfg.predict_route,
        serving_container_health_route=cfg.health_route,
        serving_container_ports=cfg.container_ports,
        serving_container_environment_variables=cfg.env_vars,
        # Metadata
        description=cfg.description,
        labels=cfg.labels,
        # Versioning
        version_aliases=[version_alias],
        version_description=cfg.version_description,
        # Attach to an existing model to create a new version;
        # model_id is only valid for brand-new model resources
        parent_model=parent_model.resource_name if parent_model else None,
        model_id=cfg.model_id if not parent_model else None,
        # Block until the LRO completes unless NO_WAIT=true
        sync=not cfg.no_wait,
    )
    return model


# ─────────────────────────────────────────────
# Entry point
# ─────────────────────────────────────────────

def main():
    try:
        cfg = Config()
    except ValueError as exc:
        logging.error(str(exc))
        sys.exit(1)

    credentials = get_credentials()

    # Initialise the SDK — all subsequent SDK calls inherit these settings
    aiplatform.init(
        project=cfg.project,
        location=cfg.location,
        credentials=credentials,
    )

    print(f"\n{'─'*60}")
    print(f"  Vertex AI Model Registration  (google-cloud-aiplatform SDK)")
    print(f"  Project  : {cfg.project}")
    print(f"  Location : {cfg.location}")
    print(f"  Model    : {cfg.display_name}")
    print(f"{'─'*60}\n")

    # ── Check for existing models with the same display name ──
    logging.info("Checking for existing models with the same display name …")
    existing = find_existing_models(cfg.display_name)

    parent_model: Model | None = None
    version_alias = "v1"

    if existing:
        parent_model = existing[0]
        logging.info(f"Found existing model: {parent_model.resource_name}")
        logging.info("Fetching version aliases across all versions …")
        all_aliases = collect_all_aliases(existing)
        version_alias = next_version_alias(all_aliases)
        logging.info(f"Existing aliases : {all_aliases}")
        logging.info(f"Next alias       : {version_alias}")
    else:
        logging.info("No existing model found — will create a new model entry.")
        logging.info(f"Initial alias    : {version_alias}")

    # ── Register ──────────────────────────────
    logging.info(f"Registering model (sync={not cfg.no_wait}) …")
    model = register_model(cfg, version_alias, parent_model)

    if cfg.no_wait:
        logging.info("Registration submitted (NO_WAIT=true). Check the Vertex AI console for status.")
        return

    print(f"\n{'─'*60}")
    print(f"  ✅  Model registered successfully!")
    print(f"  Resource : {model.resource_name}")
    print(f"  Version  : {model.version_id}  (alias: {version_alias})")
    print(f"{'─'*60}\n")


if __name__ == "__main__":
    main()
