"""Root entrypoint re-exporting unified BurnIQ Mock Enterprise Gateway (Port 8090 & /mock-enterprise)."""
from app.mock_enterprise import mock_app as app, mock_app, mock_router  # noqa: F401
