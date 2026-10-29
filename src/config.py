from pathlib import Path


# ---------------------------------------------------------
# PROJECT ROOT
# ---------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ---------------------------------------------------------
# DIRECTORIES
# ---------------------------------------------------------

DATA_DIR = PROJECT_ROOT / "data"

RAW_DIR = DATA_DIR / "raw"
INTERIM_DIR = DATA_DIR / "interim"
PROCESSED_DIR = DATA_DIR / "processed"

CONFIG_DIR = PROJECT_ROOT / "config"

OUTPUT_DIR = PROJECT_ROOT / "outputs"
FIGURES_DIR = OUTPUT_DIR / "figures"
TABLES_DIR = OUTPUT_DIR / "tables"


# ---------------------------------------------------------
# RAW DATA DIRECTORIES
# ---------------------------------------------------------

CENSUS_RAW_DIR = RAW_DIR / "census"
WNBA_RAW_DIR = RAW_DIR / "wnba"
TRENDS_RAW_DIR = RAW_DIR / "trends"
SOCIAL_RAW_DIR = RAW_DIR / "social"
MEDIA_RAW_DIR = RAW_DIR / "media"
COMMERCIAL_RAW_DIR = RAW_DIR / "commercial"


# ---------------------------------------------------------
# PROCESSED FILES
# ---------------------------------------------------------

MARKET_DATA_PATH = PROCESSED_DIR / "wnba_market_demographics.csv"

TEAM_MARKET_PATH = CONFIG_DIR / "markets.csv"


# ---------------------------------------------------------
# CENSUS SETTINGS
# ---------------------------------------------------------

CENSUS_YEAR = 2024
CENSUS_YEARS = [2019, 2024]

# ACS 5-year profile
CENSUS_BASE_URL = (
    f"https://api.census.gov/data/"
    f"{CENSUS_YEAR}/acs/acs5/profile"
)