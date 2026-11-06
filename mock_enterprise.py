"""Root entrypoint re-exporting app.mock_enterprise:mock_app and mock_router."""
from app.mock_enterprise import mock_app as app, mock_app, mock_router  # noqa: F401
