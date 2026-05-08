# Energy Dashboard - Integration Guide

This guide explains how to configure the Energy Command Center dashboard to pull real data from your Home Assistant integrations instead of using simulated data.

## Quick Start

1. Open `energy_dashboard.html` in your browser
2. Click the **⚙️ Configure** button (bottom right)
3. Enter your Home Assistant URL and API token
4. Map your sensor entities for solar, battery, grid, and load
5. Save and the dashboard will start showing live data

## Entity Mapping

The dashboard needs these core entities to function:

### Solar Power (Required for Solar Gauge)
**Entity Key**: `solar_power`  
**Unit**: kW  
**Description**: Current solar generation power

#### Integration Sources:
- **Fronius (SolarEdge API)**: `sensor.fronius_p_ac` or `sensor.solaredge_current_power`
- **Huawei**: `sensor.huawei_real_time_power`
- **Victron**: `sensor.victron_solar_power`
- **Solax X3**: `sensor.solax_pv1_power + sensor.solax_pv2_power`
- **MQTT**: `sensor.solar_power` (custom MQTT topic)
- **Local Inverter API**: Template sensor aggregating from REST API

### Battery State of Charge (Required for Battery Gauge)
**Entity Key**: `battery_soc`  
**Unit**: % (0-100)  
**Description**: Current battery state of charge

#### Integration Sources:
- **Tesla Powerwall**: `sensor.powerwall_battery_percentage`
- **Victron CCGX**: `sensor.victron_battery_state_of_charge`
- **LiFePO4 BMS**: `sensor.battery_soc`
- **Solax X3**: `sensor.solax_battery_power_soc`
- **MQTT**: `sensor.battery_soc` (from BMS over MQTT)
- **Custom**: Template sensor calculating from Ah counters

### Battery Power (Optional but Recommended)
**Entity Key**: `battery_power`  
**Unit**: kW (negative = charging, positive = discharging)  
**Description**: Current battery charge/discharge power

#### Integration Sources:
- **Tesla Powerwall**: `sensor.powerwall_charge_power`
- **Victron**: `sensor.victron_battery_power` (inverted if needed)
- **Solax**: `sensor.solax_battery_power`
- **Shelly**: Template sensor from Shelly 3EM

### Grid Power (Required for Grid Gauge)
**Entity Key**: `grid_power`  
**Unit**: kW (negative = exporting, positive = importing)  
**Description**: Current grid import/export power

#### Integration Sources:
- **Smart Meter via MQTT**: `sensor.grid_power`
- **Shelly 3EM**: `sensor.shelly_em_power` (phases summed)
- **Fronius**: Combination of inverter and meter data
- **Local Inverter**: REST template sensor
- **Volkszahler**: `sensor.volkszahler_power`
- **Sense Energy Monitor**: `sensor.sense_grid_power`

### House Load (Required for House Load Gauge)
**Entity Key**: `load_power`  
**Unit**: kW  
**Description**: Current household consumption

#### Integration Sources:
- **Shelly 3EM**: `sensor.shelly_em_internal_power`
- **Smart Meter + Solar + Battery**: Template sensor `grid_power - solar_power + battery_power`
- **Sense**: `sensor.sense_home_power`
- **Enel/Smart Meter**: Direct meter reading
- **Sum of Sub-circuits**: Aggregate from sub-metering

### Grid Renewables (Optional)
**Entity Key**: `renewables`  
**Unit**: % (0-100)  
**Description**: Percentage of grid power from renewables

#### Integration Sources:
- **Amber Energy API**: `sensor.amber_renewables`
- **Octopus Energy**: `sensor.octopus_renewables`
- **Australian NEM**: `sensor.aemo_renewables`
- **Tibber**: `sensor.tibber_renewables`
- **Static**: Set to fixed percentage based on your grid mix

### Import Price (For Cost Tracking)
**Entity Key**: `import_price`  
**Unit**: $/kWh  
**Description**: Current electricity import price

#### Integration Sources:
- **Amber Energy**: `sensor.amber_price`
- **Octopus Energy**: `sensor.octopus_electricity_rate`
- **AEMO/NEM**: Automation-based from public API
- **MQTT**: Custom integration publishing prices
- **Template**: Manual rate update via input_number

### Export Price (For Revenue Tracking)
**Entity Key**: `export_price`  
**Unit**: $/kWh  
**Description**: Current electricity export/feed-in tariff

#### Integration Sources:
- **Amber Energy**: `sensor.amber_feed_in_rate`
- **Octopus Energy**: `sensor.octopus_export_rate`
- **MQTT**: Feed-in rate from energy provider
- **Template**: Static or dynamic based on time-of-use

### Price Forecast (For 24h Chart)
**Entity Key**: `forecast`  
**Unit**: JSON array of prices for next 24 hours  
**Description**: Hourly electricity price forecast

#### Integration Sources:
- **Amber Energy**: Via custom Python script polling API
- **Tibber**: `sensor.tibber_prices` (webhook-based)
- **AEMO**: Automated daily update
- **Custom**: MQTT publishing from external service

## Configuration Examples

### Minimal Setup (Solar Only)
```
Home Assistant URL: http://homeassistant.local:8123
API Token: your_long_lived_token
Solar Power: sensor.fronius_p_ac
Battery SoC: sensor.battery_soc
Grid Power: sensor.shelly_em_power
House Load: (template: solar - grid)
```

### Complete Home Setup (All Sensors)
```
Home Assistant URL: http://homeassistant.local:8123
API Token: your_long_lived_token
Solar Power: sensor.solaredge_current_power
Battery SoC: sensor.powerwall_battery_percentage
Battery Power: sensor.powerwall_charge_power
Grid Power: sensor.shelly_3em_a_power (summed phases)
House Load: sensor.sense_home_power
Renewables: sensor.amber_renewables
Import Price: sensor.amber_price
Export Price: sensor.amber_feed_in_rate
Price Forecast: sensor.amber_forecast
```

### Off-Grid with Local Generation
```
Solar Power: sensor.pv_inverter_output
Battery SoC: sensor.bms_soc
Grid Power: 0 (off-grid, optional)
House Load: sensor.local_meter_consumption
```

## Creating Template Sensors

If your hardware doesn't directly provide a needed entity, create a template sensor:

### Example: House Load from Components
```yaml
# configuration.yaml
template:
  - sensor:
      - name: House Load
        unit_of_measurement: kW
        device_class: power
        state: >
          {% set solar = states('sensor.solar_power') | float(0) %}
          {% set grid = states('sensor.grid_power') | float(0) %}
          {% set battery = states('sensor.battery_power') | float(0) %}
          {{ ((grid - solar + battery) | float(0) * 1000) | round(2) }}
```

### Example: Total Solar from Multiple Inverters
```yaml
template:
  - sensor:
      - name: Total Solar Power
        unit_of_measurement: kW
        state: >
          {% set pv1 = states('sensor.inverter1_power') | float(0) %}
          {% set pv2 = states('sensor.inverter2_power') | float(0) %}
          {{ (pv1 + pv2) | round(2) }}
```

## Troubleshooting

### Dashboard Shows "No data" on gauges
1. Verify the entity IDs are correct in configuration
2. Check entity is available in Home Assistant (`Developer Tools > States`)
3. Ensure API token has read access to these entities
4. Check browser console for fetch errors (F12)

### Connection shows "Configuring..."
1. Verify HA URL is correct and reachable
2. Check API token is valid (generate new if needed)
3. Check CORS is allowed (should be by default)
4. Verify firewall isn't blocking the connection

### Data updates slowly
1. Increase polling frequency in the HTML (change `setInterval(updateAllEntities, 5000)`)
2. Or use Home Assistant WebSocket API for real-time updates
3. Ensure entity update frequency isn't too low in HA

### Negative/Inverted Values
Some integrations report battery power with opposite sign convention. If discharging shows as negative:
1. Create a template sensor inverting the sign
2. Or adjust the interpretation in the dashboard code

## Advanced: WebSocket for Real-Time Updates

For production deployments, replace REST polling with Home Assistant WebSocket API:

```javascript
// This requires integrating Home Assistant's WebSocket client
// See: https://developers.home-assistant.io/docs/api/websocket

const ws = new WebSocket('ws://homeassistant.local:8123/api/websocket');

ws.onmessage = (event) => {
  const msg = JSON.parse(event.data);
  if (msg.type === 'state_changed') {
    updateEntityState(msg.event.data.entity_id, msg.event.data.new_state.state);
    updateDashboard();
  }
};
```

## Integration-Specific Notes

### Fronius (SolarEdge API)
- Requires API key in Fronius integration
- Power data updates every 5-15 minutes
- Best paired with Shelly for grid/load data

### Tesla Powerwall
- Requires authentication setup
- Real-time data (1-2 second updates)
- Includes temperature and health metrics

### Amber Energy
- Provides hourly price forecasts
- Includes renewables percentage
- Requires API key from Amber dashboard

### MQTT
- Flexible - works with any MQTT-enabled hardware
- Requires MQTT broker in HA setup
- Can aggregate multiple devices (inverter + BMS + meter)

## Support

For integration-specific issues:
1. Check Home Assistant integration docs: https://www.home-assistant.io/integrations/
2. Search the Voltiq GitHub issues
3. Ask in Home Assistant Community Forums
