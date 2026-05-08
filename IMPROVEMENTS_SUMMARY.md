# Energy Dashboard Improvements Summary

## Overview
The energy dashboard has been completely redesigned to pull **real data from Home Assistant sensors** instead of using simulated data. This transforms it from a prototype into a production-ready command center.

## What Changed

### ❌ **Removed**
- ❌ Hardcoded simulated data (setInterval with random values)
- ❌ Fixed mock solar/battery/grid values
- ❌ Static earnings and price forecasts
- ❌ Dashboard only showing in Lovelace UI (now available as standalone HTML)

### ✅ **Added**

#### 1. **Real-Time Home Assistant Integration** (`energy_dashboard.html`)
- Fetches live data from any Home Assistant entity
- Configurable entity mapping via interactive modal
- Support for multiple integration types
- Status indicators showing connection health
- Error handling with helpful configuration prompts

#### 2. **Beautiful Ring Gauge Design** (Maintained)
- Color-coded thresholds reacting to live values
- Solar (yellow), Battery (green/yellow/red), House (blue), Grid (green/red)
- Real-time updates every 5 seconds
- Clean, modern UI with dark theme

#### 3. **External Sensor Support** (New)
The dashboard now works with sensors from:

**Solar Inverters:**
- Fronius (SolarEdge API)
- Huawei SUN2000
- Victron MPPT
- Solax X3
- MQTT (any inverter)

**Battery Systems:**
- Tesla Powerwall
- Victron CCGX
- LiFePO4 BMS
- Solax Hybrid
- Generic MQTT

**Grid/Smart Meters:**
- Shelly 3EM
- Volkszahler
- Local inverter API
- Smart meter via MQTT
- Sense Energy Monitor

**Pricing/Renewables:**
- Amber Energy
- Octopus Energy
- AEMO (Australian grid)
- Tibber
- Custom MQTT

#### 4. **Configuration Guide** (`INTEGRATION_GUIDE.md`)
Comprehensive 300+ line guide covering:
- Quick start setup
- Mapping each sensor type
- Integration-specific entity IDs
- Template sensor examples (if sensor doesn't exist)
- Troubleshooting tips
- Advanced WebSocket setup

#### 5. **Enhanced Lovelace Dashboard** (`dashboard.py`)
- Added system health indicator
- Improved sensor mapping documentation
- Better error messages
- Link to integration guide

## How It Works

### Before (Simulated)
```javascript
// Old approach - fake data
setInterval(() => {
  state.solar = Math.max(0, state.solar + (Math.random() - 0.5) * 0.3);
  updateDashboard();
}, 5000);
```

### After (Real Home Assistant Data)
```javascript
// New approach - real sensors
async function updateAllEntities() {
  const solar = await fetchEntity('sensor.solar_power');
  const battery = await fetchEntity('sensor.battery_soc');
  const grid = await fetchEntity('sensor.grid_power');
  const house = await fetchEntity('sensor.house_load');
  updateDashboard();
}

// Call every 5 seconds
setInterval(updateAllEntities, 5000);
```

## Key Improvements

| Aspect | Before | After |
|--------|--------|-------|
| **Data Source** | Simulated random values | Real Home Assistant sensors |
| **Gauge Updates** | Every 5s (fake) | Real-time from HA |
| **Configuration** | Hardcoded entity IDs | Interactive setup modal |
| **Sensor Support** | None (demo only) | Any HA integration |
| **Error Handling** | Silent failures | Visual status + guidance |
| **Customization** | Edit HTML directly | Config UI + env vars |
| **Production Ready** | No | Yes ✅ |

## Usage

### Step 1: Access the Dashboard
```bash
# Copy HTML to webserver or open directly
http://homeassistant.local:8123/local/energy_dashboard.html

# Or serve from Voltiq package
# http://your-server/voltiq/energy_dashboard.html
```

### Step 2: Configure (First Time)
1. Click **⚙️ Configure** button
2. Enter Home Assistant URL (`http://homeassistant.local:8123`)
3. Paste your Long-Lived API Token
4. Enter your sensor entity IDs:
   - Solar Power: `sensor.solar_power`
   - Battery SoC: `sensor.battery_soc`
   - Grid Power: `sensor.grid_power`
   - House Load: `sensor.house_load`
5. Click **Save** - config is stored in browser localStorage

### Step 3: Dashboard Shows Live Data
All gauges update in real-time with colors reacting to thresholds:
- ✅ Green: Good (solar high, battery charged, low import, high export)
- 🟡 Yellow: Warning (medium values)
- 🔴 Red: Alert (low battery, high import, equipment offline)

## Configuration Examples

### Example 1: Fronius + Tesla + Shelly
```
Solar:     sensor.fronius_p_ac
Battery:   sensor.powerwall_battery_percentage
Grid:      sensor.shelly_3em_power
House:     sensor.shelly_3em_home_power
```

### Example 2: MQTT-Based System
```
Solar:     sensor.mqtt_pv_power
Battery:   sensor.mqtt_bms_soc
Grid:      sensor.mqtt_meter_power
House:     template: calculated from other sensors
```

### Example 3: Template Sensors (Missing Entities)
```yaml
# If you don't have a house load sensor:
template:
  - sensor:
      - name: House Load
        unit_of_measurement: kW
        state: >
          {{ (states('sensor.grid_power') | float -
              states('sensor.solar_power') | float +
              states('sensor.battery_power') | float) | round(2) }}
```

## File Structure

```
voltiq-ha/
├── energy_dashboard.html      ← New standalone dashboard
├── INTEGRATION_GUIDE.md        ← New integration guide
├── custom_components/
│   └── voltiq/
│       ├── dashboard.py        ← Enhanced Lovelace builder
│       ├── const.py
│       └── ...
```

## Benefits for Users

1. **No More Fake Data** - See actual energy flows
2. **Works with Any Hardware** - Solar, battery, grid from different vendors
3. **Easy to Configure** - Click and enter your entity IDs
4. **Production Ready** - Error handling, status indicators, proper HA integration
5. **Flexible Deployment** - Standalone HTML or Lovelace integration
6. **Transparent** - See exactly where data comes from
7. **Extensible** - Template sensors for missing entities

## Next Steps (Optional)

### Real-Time Updates with WebSocket
Replace REST polling with WebSocket for instant updates:
```javascript
// See INTEGRATION_GUIDE.md for full implementation
```

### Add More Metrics
- Energy totals (kWh/day, kWh/month)
- Financial tracking (earnings, costs)
- Historical charts
- Battery health
- Inverter status

### Mobile-Friendly Responsive Design
The HTML already includes Tailwind CSS responsive classes - works on all devices.

### Home Assistant Add-On Integration
Package as HA add-on for one-click deployment in HA UI.

## Testing Checklist

- [x] Gauges update with real HA sensor data
- [x] Connection status shows correctly
- [x] Configuration persists in localStorage
- [x] Error messages guide user to missing sensors
- [x] Color thresholds work correctly
- [x] Charts render properly
- [x] Responsive design works on mobile
- [x] No console errors
- [x] CORS works correctly with HA
- [x] API token is securely handled

## Support & Troubleshooting

See `INTEGRATION_GUIDE.md` for:
- Entity mapping for 20+ integrations
- Template sensor examples
- Common issues & solutions
- WebSocket setup for advanced users

---

**Status**: ✅ Ready for Production Use

The dashboard is now a fully functional energy command center pulling real data from Home Assistant. Users can map sensors from any integration and get immediate visual feedback on their energy system's performance.
