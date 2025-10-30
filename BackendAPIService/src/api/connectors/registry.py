"""
Connector registry providing discovery of available connectors.

For bootstrap, this returns a static list for Jira and Confluence.
Later, this can be populated via module loading or build-time registration.
"""
from __future__ import annotations

from typing import List

from .base import ConnectorCapability, ConnectorMetadata


# PUBLIC_INTERFACE
def list_connectors() -> List[ConnectorMetadata]:
    """Return the list of available connector metadata (static bootstrap)."""
    jira = ConnectorMetadata(
        name="jira",
        title="Jira Software",
        description="Integrate with Jira to search and create issues.",
        status="beta",
        categories=["atlassian", "issues"],
        capabilities=[
            ConnectorCapability(key="search", description="Search issues"),
            ConnectorCapability(key="create_issue", description="Create issues"),
        ],
        docs_url="https://developer.atlassian.com/cloud/jira/platform/rest/v3/intro/",
    )
    confluence = ConnectorMetadata(
        name="confluence",
        title="Confluence",
        description="Integrate with Confluence to search and create pages.",
        status="beta",
        categories=["atlassian", "knowledge"],
        capabilities=[
            ConnectorCapability(key="search", description="Search pages"),
            ConnectorCapability(key="create_page", description="Create pages"),
        ],
        docs_url="https://developer.atlassian.com/cloud/confluence/rest/",
    )
    return [jira, confluence]
