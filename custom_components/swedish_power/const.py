"""Constants for the Sweden-only Swedish Power integration."""

from datetime import timedelta

DOMAIN = "swedish_power"
ENTRY_UNIQUE_ID = "sweden"
SOURCE = "Statnett Driftsdata"
SOURCE_URL = "https://driftsdata.statnett.no/restapi"
PRODUCTION_PATH = "/ProductionConsumption/GetLatestDetailedOverview"
FLOWS_PATH = "/PhysicalFlowMap/GetFlow"

UPDATE_INTERVAL = timedelta(minutes=15)
# Provisional per-source freshness cutoff; independent of polling interval.
MAX_DATA_AGE = timedelta(minutes=90)
MAX_CLOCK_SKEW = timedelta(minutes=10)
REQUEST_TIMEOUT_SECONDS = 15

METRIC_FIELDS: dict[str, str] = {
    "production": "ProductionData",
    "consumption": "ConsumptionData",
    "net_exchange": "NetExchangeData",
    "hydro": "HydroData",
    "wind": "WindData",
    "nuclear": "NuclearData",
    "thermal": "ThermalData",
    "other": "NotSpecifiedData",
}
SE_AREAS = frozenset({"SE1", "SE2", "SE3", "SE4"})
