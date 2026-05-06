"""Constants for the Voltiq Energy Manager integration."""

DOMAIN = "voltiq"
MANUFACTURER = "Voltiq"

# Config entry keys
CONF_BACKEND_URL = "backend_url"
CONF_SUPABASE_URL = "supabase_url"
CONF_SUPABASE_KEY = "supabase_anon_key"
CONF_RETAILER = "retailer"
CONF_AMBER_KEY = "amber_api_key"
CONF_LV_KEY = "localvolts_key"
CONF_LV_NMI = "localvolts_nmi"
CONF_LV_PARTNER = "localvolts_partner_id"
CONF_AEMO_REGION = "aemo_region"
CONF_LATITUDE = "latitude"
CONF_LONGITUDE = "longitude"
CONF_SOLAR_CAPACITY = "solar_capacity_kw"

# Update intervals (seconds)
POLL_INTERVAL_PRICES = 60
POLL_INTERVAL_DEVICES = 15
POLL_INTERVAL_FORECAST = 1800

# Retailers
RETAILER_AEMO = "aemo"
RETAILER_AMBER = "amber"
RETAILER_LOCALVOLTS = "localvolts"

AEMO_REGIONS = {
    "NSW1": "New South Wales",
    "VIC1": "Victoria",
    "QLD1": "Queensland",
    "SA1": "South Australia",
    "TAS1": "Tasmania",
}

# Battery dispatch modes (coordinator key -> HA label)
BATTERY_MODES = {
    "self_consumption": "Self Consumption",
    "feed_in": "Max Export",
    "forced_charge": "Force Charge",
    "forced_discharge": "Force Discharge",
    "hold": "Hold SoC",
}

# User-mapped external entity keys (options flow)
CONF_ENTITY_SOLAR_POWER = "entity_solar_power"
CONF_ENTITY_BATTERY_SOC = "entity_battery_soc"
CONF_ENTITY_BATTERY_POWER = "entity_battery_power"
CONF_ENTITY_GRID_POWER = "entity_grid_power"
CONF_ENTITY_LOAD_POWER = "entity_load_power"
CONF_ENTITY_GRID_IMPORT = "entity_grid_import"
CONF_ENTITY_GRID_EXPORT = "entity_grid_export"
CONF_ENTITY_SOLAR_ENERGY = "entity_solar_energy"
CONF_ENTITY_BATTERY_ENERGY_IN = "entity_battery_energy_in"
CONF_ENTITY_BATTERY_ENERGY_OUT = "entity_battery_energy_out"
CONF_ENTITY_SOLAR_FORECAST = "entity_solar_forecast"
CONF_ENTITY_IMPORT_PRICE = "entity_import_price"
CONF_ENTITY_EXPORT_PRICE = "entity_export_price"
CONF_DASHBOARD_ENABLED = "dashboard_enabled"

DASHBOARD_URL_PATH = "voltiq-energy"
DASHBOARD_TITLE = "Voltiq Energy"

# Coordinator data section keys
DATA_PRICES = "prices"
DATA_SYSTEM = "system"
DATA_EARNINGS = "earnings"
DATA_ALERTS = "alerts"
DATA_ADVISOR = "advisor"
DATA_SETTINGS = "db_settings"
DATA_FORECAST = "forecast"
