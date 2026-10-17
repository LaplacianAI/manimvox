import os

# haystack builds its telemetry client when first imported, so this must be set before any test imports it
os.environ.setdefault("HAYSTACK_TELEMETRY_ENABLED", "False")
os.environ.setdefault("CREWAI_DISABLE_TELEMETRY", "true")
os.environ.setdefault("AGNO_TELEMETRY", "false")
