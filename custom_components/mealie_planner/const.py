"""Constants for Mealie Planner."""

from __future__ import annotations

DOMAIN = "mealie_planner"

# Connection, in the config entry's data.
CONF_MEALIE_URL = "mealie_url"
CONF_MEALIE_TOKEN = "mealie_token"
CONF_AI_BASE_URL = "ai_base_url"
CONF_AI_KEY = "ai_api_key"
CONF_AI_MODEL = "ai_model"

DEFAULT_AI_BASE_URL = "https://api.openai.com/v1"
DEFAULT_AI_MODEL = "gpt-4o-mini"

# Behaviour, in the config entry's options.
OPT_PLANNER_MODE = "planner_mode"
OPT_WEB_CHAINS = "web_chains"
OPT_BROCHURE_CHAINS = "brochure_chains"
OPT_LIST_ENTRY = "list_entry"
OPT_WEEK_START = "week_start"
OPT_MAX_PAGES = "max_pages"
OPT_ZONE_PREFIX = "zone_"
OPT_BROCHURE_URL_PREFIX = "brochure_url_"

MODE_LOCAL = "local"
MODE_AI = "ai"

LIDL = "lidl"
KAUFLAND = "kaufland"
BILLA = "billa"
CHAINS = (LIDL, KAUFLAND, BILLA)
CHAIN_NAMES = {LIDL: "Lidl", KAUFLAND: "Kaufland", BILLA: "Billa"}

# Where each chain's printed brochure is looked for. The page is searched for
# leaflet viewer links and PDFs; each one can be changed in the options.
DEFAULT_BROCHURE_URLS = {
    LIDL: "https://www.lidl.bg/c/broshura/s10020060",
    KAUFLAND: "https://www.kaufland.bg/broshuri.html",
    BILLA: "https://www.billa.bg/promocii/sedmichna-broshura",
}

DEFAULT_MAX_PAGES = 40
DEFAULT_WEEK_START = 0  # Monday

MEAL_TYPES = ("breakfast", "lunch", "dinner", "side", "snack", "dessert", "drink")

# Normalized offer categories. The keyword table and the AI both use these.
CATEGORIES = (
    "fish",
    "meat",
    "vegetables",
    "fruit",
    "dairy",
    "legumes",
    "bakery",
    "pantry",
    "frozen",
    "drinks",
    "other_food",
    "non_food",
)

LISTS_API = "homebasket_lists_api"
