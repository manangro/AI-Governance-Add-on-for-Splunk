"""AI Governance Add-on for Splunk - shared constants."""

ADDON_NAME = "TA-ai-governance"

SETTINGS_CONF = "ta-ai-governance_settings"
ACCOUNT_CONF = "ta-ai-governance_account"
CHECKPOINT_COLLECTION = "ta_ai_governance_checkpoints"

# Providers
PROVIDER_ANTHROPIC = "anthropic"
PROVIDER_OPENAI = "openai"
PROVIDER_GEMINI = "gemini"
PROVIDER_MICROSOFT = "microsoft"

# Sourcetypes
ST_ANTHROPIC_ACTIVITY = "aigov:anthropic:activity"
ST_ANTHROPIC_USER = "aigov:anthropic:user"
ST_ANTHROPIC_GROUP = "aigov:anthropic:group"
ST_ANTHROPIC_USAGE = "aigov:anthropic:usage"
ST_ANTHROPIC_COST = "aigov:anthropic:cost"
ST_ANTHROPIC_SUMMARY = "aigov:anthropic:summary"

ST_OPENAI_AUDIT = "aigov:openai:audit"
ST_OPENAI_USER = "aigov:openai:user"
ST_OPENAI_USAGE = "aigov:openai:usage"
ST_OPENAI_COST = "aigov:openai:cost"

ST_GEMINI_AUDIT = "aigov:gemini:audit"

ST_COPILOT_INTERACTION = "aigov:copilot:interaction"
ST_COPILOT_USAGE = "aigov:copilot:usage"

# API base URLs (HTTPS only)
ANTHROPIC_API_BASE = "https://api.anthropic.com"
ANTHROPIC_VERSION = "2023-06-01"
OPENAI_API_BASE = "https://api.openai.com"
GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_REPORTS_BASE = "https://admin.googleapis.com"
MS_LOGIN_BASE = "https://login.microsoftonline.com"
MS_GRAPH_BASE = "https://graph.microsoft.com"
