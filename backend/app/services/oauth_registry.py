"""OAuth provider registry — defines all available app integrations."""

from __future__ import annotations

import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class OAuthProvider:
    provider_id: str
    display_name: str
    icon: str
    category: str
    description: str
    # OAuth endpoints
    auth_url: str = ""
    token_url: str = ""
    scopes: list[str] = field(default_factory=list)
    # Env var names for client credentials
    client_id_env: str = ""
    client_secret_env: str = ""
    # Optional
    userinfo_url: str = ""
    supports_sync: bool = False
    extra_auth_params: dict[str, str] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Provider definitions (~40 apps across 8 categories)
# ---------------------------------------------------------------------------

_PROVIDERS: list[OAuthProvider] = [
    # ── Productivity ──────────────────────────────────────────────────────
    OAuthProvider(
        provider_id="notion",
        display_name="Notion",
        icon="https://cdn.simpleicons.org/notion/000000",
        category="Productivity",
        description="Connect your Notion workspace to sync pages and databases.",
        auth_url="https://api.notion.com/v1/oauth/authorize",
        token_url="https://api.notion.com/v1/oauth/token",
        scopes=[],
        client_id_env="NOTION_OAUTH_CLIENT_ID",
        client_secret_env="NOTION_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.notion.com/v1/users/me",
        supports_sync=True,
        extra_auth_params={"owner": "user"},
    ),
    OAuthProvider(
        provider_id="google_drive",
        display_name="Google Drive",
        icon="https://cdn.simpleicons.org/googledrive",
        category="Productivity",
        description="Access and sync files from Google Drive.",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/drive.readonly", "openid", "email", "profile"],
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        extra_auth_params={"access_type": "offline", "prompt": "consent"},
    ),
    OAuthProvider(
        provider_id="google_docs",
        display_name="Google Docs",
        icon="https://cdn.simpleicons.org/googledocs",
        category="Productivity",
        description="Import content from Google Docs.",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/documents.readonly", "openid", "email", "profile"],
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        extra_auth_params={"access_type": "offline", "prompt": "consent"},
    ),
    OAuthProvider(
        provider_id="onedrive",
        display_name="OneDrive",
        icon="https://cdn.simpleicons.org/microsoftonedrive",
        category="Productivity",
        description="Sync files from Microsoft OneDrive.",
        auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        scopes=["Files.Read.All", "User.Read", "offline_access"],
        client_id_env="MICROSOFT_OAUTH_CLIENT_ID",
        client_secret_env="MICROSOFT_OAUTH_CLIENT_SECRET",
        userinfo_url="https://graph.microsoft.com/v1.0/me",
    ),
    OAuthProvider(
        provider_id="dropbox",
        display_name="Dropbox",
        icon="https://cdn.simpleicons.org/dropbox",
        category="Productivity",
        description="Access files stored in Dropbox.",
        auth_url="https://www.dropbox.com/oauth2/authorize",
        token_url="https://api.dropboxapi.com/oauth2/token",
        scopes=[],
        client_id_env="DROPBOX_OAUTH_CLIENT_ID",
        client_secret_env="DROPBOX_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.dropboxapi.com/2/users/get_current_account",
        extra_auth_params={"token_access_type": "offline"},
    ),
    OAuthProvider(
        provider_id="box",
        display_name="Box",
        icon="https://cdn.simpleicons.org/box",
        category="Productivity",
        description="Sync content from Box cloud storage.",
        auth_url="https://account.box.com/api/oauth2/authorize",
        token_url="https://api.box.com/oauth2/token",
        scopes=[],
        client_id_env="BOX_OAUTH_CLIENT_ID",
        client_secret_env="BOX_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.box.com/2.0/users/me",
    ),
    OAuthProvider(
        provider_id="airtable",
        display_name="Airtable",
        icon="https://cdn.simpleicons.org/airtable",
        category="Productivity",
        description="Connect Airtable bases and tables.",
        auth_url="https://airtable.com/oauth2/v1/authorize",
        token_url="https://airtable.com/oauth2/v1/token",
        scopes=["data.records:read", "schema.bases:read"],
        client_id_env="AIRTABLE_OAUTH_CLIENT_ID",
        client_secret_env="AIRTABLE_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.airtable.com/v0/meta/whoami",
    ),
    OAuthProvider(
        provider_id="coda",
        display_name="Coda",
        icon="https://cdn.simpleicons.org/coda",
        category="Productivity",
        description="Import docs from Coda.",
        auth_url="https://coda.io/oauth/authorize",
        token_url="https://coda.io/oauth/token",
        scopes=["doc:read"],
        client_id_env="CODA_OAUTH_CLIENT_ID",
        client_secret_env="CODA_OAUTH_CLIENT_SECRET",
        userinfo_url="https://coda.io/apis/v1/whoami",
    ),

    # ── Communication ─────────────────────────────────────────────────────
    OAuthProvider(
        provider_id="slack",
        display_name="Slack",
        icon="https://cdn.simpleicons.org/slack",
        category="Communication",
        description="Connect Slack to index channel messages and threads.",
        auth_url="https://slack.com/oauth/v2/authorize",
        token_url="https://slack.com/api/oauth.v2.access",
        scopes=["channels:read", "channels:history", "users:read"],
        client_id_env="SLACK_OAUTH_CLIENT_ID",
        client_secret_env="SLACK_OAUTH_CLIENT_SECRET",
        userinfo_url="https://slack.com/api/auth.test",
    ),
    OAuthProvider(
        provider_id="microsoft_teams",
        display_name="Microsoft Teams",
        icon="https://cdn.simpleicons.org/microsoftteams",
        category="Communication",
        description="Sync conversations from Microsoft Teams.",
        auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        scopes=["Chat.Read", "User.Read", "offline_access"],
        client_id_env="MICROSOFT_OAUTH_CLIENT_ID",
        client_secret_env="MICROSOFT_OAUTH_CLIENT_SECRET",
        userinfo_url="https://graph.microsoft.com/v1.0/me",
    ),
    OAuthProvider(
        provider_id="gmail",
        display_name="Gmail",
        icon="https://cdn.simpleicons.org/gmail",
        category="Communication",
        description="Index emails from Gmail.",
        auth_url="https://accounts.google.com/o/oauth2/v2/auth",
        token_url="https://oauth2.googleapis.com/token",
        scopes=["https://www.googleapis.com/auth/gmail.readonly", "openid", "email", "profile"],
        client_id_env="GOOGLE_OAUTH_CLIENT_ID",
        client_secret_env="GOOGLE_OAUTH_CLIENT_SECRET",
        userinfo_url="https://www.googleapis.com/oauth2/v2/userinfo",
        extra_auth_params={"access_type": "offline", "prompt": "consent"},
    ),
    OAuthProvider(
        provider_id="outlook",
        display_name="Outlook",
        icon="https://cdn.simpleicons.org/microsoftoutlook",
        category="Communication",
        description="Sync emails from Outlook.",
        auth_url="https://login.microsoftonline.com/common/oauth2/v2.0/authorize",
        token_url="https://login.microsoftonline.com/common/oauth2/v2.0/token",
        scopes=["Mail.Read", "User.Read", "offline_access"],
        client_id_env="MICROSOFT_OAUTH_CLIENT_ID",
        client_secret_env="MICROSOFT_OAUTH_CLIENT_SECRET",
        userinfo_url="https://graph.microsoft.com/v1.0/me",
    ),
    OAuthProvider(
        provider_id="discord",
        display_name="Discord",
        icon="https://cdn.simpleicons.org/discord",
        category="Communication",
        description="Connect Discord servers and channels.",
        auth_url="https://discord.com/oauth2/authorize",
        token_url="https://discord.com/api/oauth2/token",
        scopes=["identify", "guilds"],
        client_id_env="DISCORD_OAUTH_CLIENT_ID",
        client_secret_env="DISCORD_OAUTH_CLIENT_SECRET",
        userinfo_url="https://discord.com/api/users/@me",
    ),
    OAuthProvider(
        provider_id="zoom",
        display_name="Zoom",
        icon="https://cdn.simpleicons.org/zoom",
        category="Communication",
        description="Sync Zoom meeting transcripts.",
        auth_url="https://zoom.us/oauth/authorize",
        token_url="https://zoom.us/oauth/token",
        scopes=[],
        client_id_env="ZOOM_OAUTH_CLIENT_ID",
        client_secret_env="ZOOM_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.zoom.us/v2/users/me",
    ),

    # ── Project Management ────────────────────────────────────────────────
    OAuthProvider(
        provider_id="jira",
        display_name="Jira",
        icon="https://cdn.simpleicons.org/jira",
        category="Project Management",
        description="Connect Jira to sync issues and projects.",
        auth_url="https://auth.atlassian.com/authorize",
        token_url="https://auth.atlassian.com/oauth/token",
        scopes=["read:jira-work", "read:jira-user", "offline_access"],
        client_id_env="ATLASSIAN_OAUTH_CLIENT_ID",
        client_secret_env="ATLASSIAN_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.atlassian.com/me",
        extra_auth_params={"audience": "api.atlassian.com", "prompt": "consent"},
    ),
    OAuthProvider(
        provider_id="confluence",
        display_name="Confluence",
        icon="https://cdn.simpleicons.org/confluence",
        category="Project Management",
        description="Sync Confluence pages and spaces.",
        auth_url="https://auth.atlassian.com/authorize",
        token_url="https://auth.atlassian.com/oauth/token",
        scopes=["read:confluence-content.all", "read:confluence-user", "offline_access"],
        client_id_env="ATLASSIAN_OAUTH_CLIENT_ID",
        client_secret_env="ATLASSIAN_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.atlassian.com/me",
        extra_auth_params={"audience": "api.atlassian.com", "prompt": "consent"},
    ),
    OAuthProvider(
        provider_id="asana",
        display_name="Asana",
        icon="https://cdn.simpleicons.org/asana",
        category="Project Management",
        description="Import tasks and projects from Asana.",
        auth_url="https://app.asana.com/-/oauth_authorize",
        token_url="https://app.asana.com/-/oauth_token",
        scopes=[],
        client_id_env="ASANA_OAUTH_CLIENT_ID",
        client_secret_env="ASANA_OAUTH_CLIENT_SECRET",
        userinfo_url="https://app.asana.com/api/1.0/users/me",
    ),
    OAuthProvider(
        provider_id="trello",
        display_name="Trello",
        icon="https://cdn.simpleicons.org/trello",
        category="Project Management",
        description="Sync Trello boards and cards.",
        auth_url="https://trello.com/1/authorize",
        token_url="https://trello.com/1/OAuthGetAccessToken",
        scopes=["read"],
        client_id_env="TRELLO_OAUTH_CLIENT_ID",
        client_secret_env="TRELLO_OAUTH_CLIENT_SECRET",
    ),
    OAuthProvider(
        provider_id="linear",
        display_name="Linear",
        icon="https://cdn.simpleicons.org/linear",
        category="Project Management",
        description="Connect Linear to sync issues and projects.",
        auth_url="https://linear.app/oauth/authorize",
        token_url="https://api.linear.app/oauth/token",
        scopes=["read"],
        client_id_env="LINEAR_OAUTH_CLIENT_ID",
        client_secret_env="LINEAR_OAUTH_CLIENT_SECRET",
    ),
    OAuthProvider(
        provider_id="monday",
        display_name="Monday.com",
        icon="https://cdn.simpleicons.org/mondaydotcom",
        category="Project Management",
        description="Sync boards and items from Monday.com.",
        auth_url="https://auth.monday.com/oauth2/authorize",
        token_url="https://auth.monday.com/oauth2/token",
        scopes=[],
        client_id_env="MONDAY_OAUTH_CLIENT_ID",
        client_secret_env="MONDAY_OAUTH_CLIENT_SECRET",
    ),
    OAuthProvider(
        provider_id="clickup",
        display_name="ClickUp",
        icon="https://cdn.simpleicons.org/clickup",
        category="Project Management",
        description="Import tasks and docs from ClickUp.",
        auth_url="https://app.clickup.com/api",
        token_url="https://api.clickup.com/api/v2/oauth/token",
        scopes=[],
        client_id_env="CLICKUP_OAUTH_CLIENT_ID",
        client_secret_env="CLICKUP_OAUTH_CLIENT_SECRET",
    ),

    # ── Developer Tools ───────────────────────────────────────────────────
    OAuthProvider(
        provider_id="github",
        display_name="GitHub",
        icon="https://cdn.simpleicons.org/github/000000",
        category="Developer Tools",
        description="Index repositories and documentation from GitHub.",
        auth_url="https://github.com/login/oauth/authorize",
        token_url="https://github.com/login/oauth/access_token",
        scopes=["read:user", "repo"],
        client_id_env="GITHUB_OAUTH_CLIENT_ID",
        client_secret_env="GITHUB_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.github.com/user",
    ),
    OAuthProvider(
        provider_id="gitlab",
        display_name="GitLab",
        icon="https://cdn.simpleicons.org/gitlab",
        category="Developer Tools",
        description="Sync repositories from GitLab.",
        auth_url="https://gitlab.com/oauth/authorize",
        token_url="https://gitlab.com/oauth/token",
        scopes=["read_user", "read_api"],
        client_id_env="GITLAB_OAUTH_CLIENT_ID",
        client_secret_env="GITLAB_OAUTH_CLIENT_SECRET",
        userinfo_url="https://gitlab.com/api/v4/user",
    ),
    OAuthProvider(
        provider_id="bitbucket",
        display_name="Bitbucket",
        icon="https://cdn.simpleicons.org/bitbucket",
        category="Developer Tools",
        description="Connect Bitbucket repositories.",
        auth_url="https://bitbucket.org/site/oauth2/authorize",
        token_url="https://bitbucket.org/site/oauth2/access_token",
        scopes=["repository", "account"],
        client_id_env="BITBUCKET_OAUTH_CLIENT_ID",
        client_secret_env="BITBUCKET_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.bitbucket.org/2.0/user",
    ),
    OAuthProvider(
        provider_id="figma",
        display_name="Figma",
        icon="https://cdn.simpleicons.org/figma",
        category="Developer Tools",
        description="Access Figma files and design data.",
        auth_url="https://www.figma.com/oauth",
        token_url="https://www.figma.com/api/oauth/token",
        scopes=["file_read"],
        client_id_env="FIGMA_OAUTH_CLIENT_ID",
        client_secret_env="FIGMA_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.figma.com/v1/me",
    ),

    # ── CRM & Sales ───────────────────────────────────────────────────────
    OAuthProvider(
        provider_id="salesforce",
        display_name="Salesforce",
        icon="https://cdn.simpleicons.org/salesforce",
        category="CRM & Sales",
        description="Sync contacts, leads, and knowledge from Salesforce.",
        auth_url="https://login.salesforce.com/services/oauth2/authorize",
        token_url="https://login.salesforce.com/services/oauth2/token",
        scopes=["api", "refresh_token"],
        client_id_env="SALESFORCE_OAUTH_CLIENT_ID",
        client_secret_env="SALESFORCE_OAUTH_CLIENT_SECRET",
        userinfo_url="https://login.salesforce.com/services/oauth2/userinfo",
    ),
    OAuthProvider(
        provider_id="hubspot",
        display_name="HubSpot",
        icon="https://cdn.simpleicons.org/hubspot",
        category="CRM & Sales",
        description="Connect HubSpot CRM data.",
        auth_url="https://app.hubspot.com/oauth/authorize",
        token_url="https://api.hubapi.com/oauth/v1/token",
        scopes=["crm.objects.contacts.read"],
        client_id_env="HUBSPOT_OAUTH_CLIENT_ID",
        client_secret_env="HUBSPOT_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.hubapi.com/oauth/v1/access-tokens/",
    ),
    OAuthProvider(
        provider_id="pipedrive",
        display_name="Pipedrive",
        icon="https://cdn.simpleicons.org/pipedrive",
        category="CRM & Sales",
        description="Sync deals and contacts from Pipedrive.",
        auth_url="https://oauth.pipedrive.com/oauth/authorize",
        token_url="https://oauth.pipedrive.com/oauth/token",
        scopes=[],
        client_id_env="PIPEDRIVE_OAUTH_CLIENT_ID",
        client_secret_env="PIPEDRIVE_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.pipedrive.com/v1/users/me",
    ),
    OAuthProvider(
        provider_id="zoho_crm",
        display_name="Zoho CRM",
        icon="https://cdn.simpleicons.org/zoho",
        category="CRM & Sales",
        description="Connect your Zoho CRM account.",
        auth_url="https://accounts.zoho.com/oauth/v2/auth",
        token_url="https://accounts.zoho.com/oauth/v2/token",
        scopes=["ZohoCRM.modules.ALL"],
        client_id_env="ZOHO_OAUTH_CLIENT_ID",
        client_secret_env="ZOHO_OAUTH_CLIENT_SECRET",
        userinfo_url="https://www.zohoapis.com/crm/v2/users?type=CurrentUser",
    ),

    # ── Support ───────────────────────────────────────────────────────────
    OAuthProvider(
        provider_id="zendesk",
        display_name="Zendesk",
        icon="https://cdn.simpleicons.org/zendesk",
        category="Support",
        description="Sync Zendesk tickets and help center articles.",
        auth_url="https://d3v-yoursubdomain.zendesk.com/oauth/authorizations/new",
        token_url="https://d3v-yoursubdomain.zendesk.com/oauth/tokens",
        scopes=["read"],
        client_id_env="ZENDESK_OAUTH_CLIENT_ID",
        client_secret_env="ZENDESK_OAUTH_CLIENT_SECRET",
    ),
    OAuthProvider(
        provider_id="intercom",
        display_name="Intercom",
        icon="https://cdn.simpleicons.org/intercom",
        category="Support",
        description="Connect Intercom conversations and articles.",
        auth_url="https://app.intercom.com/oauth",
        token_url="https://api.intercom.io/auth/eagle/token",
        scopes=[],
        client_id_env="INTERCOM_OAUTH_CLIENT_ID",
        client_secret_env="INTERCOM_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.intercom.io/me",
    ),
    OAuthProvider(
        provider_id="freshdesk",
        display_name="Freshdesk",
        icon="https://cdn.simpleicons.org/freshdesk",
        category="Support",
        description="Sync Freshdesk tickets and solutions.",
        auth_url="",
        token_url="",
        scopes=[],
        client_id_env="FRESHDESK_OAUTH_CLIENT_ID",
        client_secret_env="FRESHDESK_OAUTH_CLIENT_SECRET",
    ),
    OAuthProvider(
        provider_id="helpscout",
        display_name="Help Scout",
        icon="https://cdn.simpleicons.org/helpscout",
        category="Support",
        description="Connect Help Scout mailboxes and docs.",
        auth_url="https://secure.helpscout.net/authentication/authorizeClientApplication",
        token_url="https://api.helpscout.net/v2/oauth2/token",
        scopes=[],
        client_id_env="HELPSCOUT_OAUTH_CLIENT_ID",
        client_secret_env="HELPSCOUT_OAUTH_CLIENT_SECRET",
    ),

    # ── Social Media ──────────────────────────────────────────────────────
    OAuthProvider(
        provider_id="instagram",
        display_name="Instagram",
        icon="https://cdn.simpleicons.org/instagram",
        category="Social Media",
        description="Connect your Instagram business account.",
        auth_url="https://api.instagram.com/oauth/authorize",
        token_url="https://api.instagram.com/oauth/access_token",
        scopes=["user_profile", "user_media"],
        client_id_env="INSTAGRAM_OAUTH_CLIENT_ID",
        client_secret_env="INSTAGRAM_OAUTH_CLIENT_SECRET",
    ),
    OAuthProvider(
        provider_id="facebook",
        display_name="Facebook",
        icon="https://cdn.simpleicons.org/facebook",
        category="Social Media",
        description="Connect Facebook pages and data.",
        auth_url="https://www.facebook.com/v18.0/dialog/oauth",
        token_url="https://graph.facebook.com/v18.0/oauth/access_token",
        scopes=["pages_read_engagement", "public_profile"],
        client_id_env="FACEBOOK_OAUTH_CLIENT_ID",
        client_secret_env="FACEBOOK_OAUTH_CLIENT_SECRET",
        userinfo_url="https://graph.facebook.com/me?fields=id,name,email",
    ),
    OAuthProvider(
        provider_id="twitter",
        display_name="Twitter / X",
        icon="https://cdn.simpleicons.org/x/000000",
        category="Social Media",
        description="Connect your X (Twitter) account.",
        auth_url="https://twitter.com/i/oauth2/authorize",
        token_url="https://api.twitter.com/2/oauth2/token",
        scopes=["tweet.read", "users.read", "offline.access"],
        client_id_env="TWITTER_OAUTH_CLIENT_ID",
        client_secret_env="TWITTER_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.twitter.com/2/users/me",
    ),
    OAuthProvider(
        provider_id="linkedin",
        display_name="LinkedIn",
        icon="https://cdn.simpleicons.org/linkedin",
        category="Social Media",
        description="Connect your LinkedIn profile.",
        auth_url="https://www.linkedin.com/oauth/v2/authorization",
        token_url="https://www.linkedin.com/oauth/v2/accessToken",
        scopes=["openid", "profile", "email"],
        client_id_env="LINKEDIN_OAUTH_CLIENT_ID",
        client_secret_env="LINKEDIN_OAUTH_CLIENT_SECRET",
        userinfo_url="https://api.linkedin.com/v2/userinfo",
    ),

    # ── Other ─────────────────────────────────────────────────────────────
    OAuthProvider(
        provider_id="shopify",
        display_name="Shopify",
        icon="https://cdn.simpleicons.org/shopify",
        category="Other",
        description="Sync product and store data from Shopify.",
        auth_url="https://{shop}.myshopify.com/admin/oauth/authorize",
        token_url="https://{shop}.myshopify.com/admin/oauth/access_token",
        scopes=["read_products", "read_content"],
        client_id_env="SHOPIFY_OAUTH_CLIENT_ID",
        client_secret_env="SHOPIFY_OAUTH_CLIENT_SECRET",
    ),
    OAuthProvider(
        provider_id="stripe",
        display_name="Stripe",
        icon="https://cdn.simpleicons.org/stripe",
        category="Other",
        description="Connect Stripe for payment data.",
        auth_url="https://connect.stripe.com/oauth/authorize",
        token_url="https://connect.stripe.com/oauth/token",
        scopes=["read_only"],
        client_id_env="STRIPE_OAUTH_CLIENT_ID",
        client_secret_env="STRIPE_OAUTH_CLIENT_SECRET",
    ),
    OAuthProvider(
        provider_id="custom",
        display_name="Custom",
        icon="",
        category="Other",
        description="Add a custom integration with manual credentials.",
        auth_url="",
        token_url="",
    ),
]

# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

_REGISTRY: dict[str, OAuthProvider] = {p.provider_id: p for p in _PROVIDERS}


def get_provider(provider_id: str) -> OAuthProvider | None:
    return _REGISTRY.get(provider_id)


def get_all_providers() -> list[OAuthProvider]:
    return list(_PROVIDERS)


def is_provider_configured(provider: OAuthProvider) -> bool:
    """Return True if the provider's OAuth client credentials are set in env vars."""
    if provider.provider_id == "custom":
        return True
    if not provider.client_id_env or not provider.client_secret_env:
        return False
    return bool(os.getenv(provider.client_id_env)) and bool(os.getenv(provider.client_secret_env))


def has_oauth_support(provider: OAuthProvider) -> bool:
    """Return True if the provider has OAuth endpoints defined (connectable in UI)."""
    return bool(provider.auth_url and provider.token_url)


def get_all_categories() -> list[str]:
    seen: set[str] = set()
    cats: list[str] = []
    for p in _PROVIDERS:
        if p.category not in seen:
            seen.add(p.category)
            cats.append(p.category)
    return cats
