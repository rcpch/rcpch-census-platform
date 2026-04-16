"""
Custom PostGIS database backend that fetches a fresh Azure Entra ID
(Managed Identity) token on every new connection, instead of once at
Django startup.  This prevents "access token has expired" errors when
Azure AD tokens (~1 hour TTL) expire while the process is still running.
"""

import os

from django.contrib.gis.db.backends.postgis.base import (
    DatabaseWrapper as PostGISWrapper,
)


class DatabaseWrapper(PostGISWrapper):
    def get_connection_params(self):
        params = super().get_connection_params()

        # Only swap in a fresh token in non-debug (production) mode.
        if not self.settings_dict.get("DEBUG", False) and not (
            os.environ.get("DEBUG", "False") == "True"
        ):
            try:
                from azure.identity import DefaultAzureCredential

                scope = "https://ossrdbms-aad.database.windows.net/.default"
                credential = DefaultAzureCredential()
                token = credential.get_token(scope)
                params["password"] = token.token
            except Exception as e:
                print(f"[db_backend] Failed to fetch Entra ID token: {e}")
                # Fall back to whatever PASSWORD is set in DATABASES
        return params
