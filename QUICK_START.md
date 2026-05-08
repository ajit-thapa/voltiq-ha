# Energy Dashboard Quick Start

## 30-Second Setup

### 1. Open Dashboard
Open `energy_dashboard.html` in your browser, or navigate to:
```
http://homeassistant.local:8123/local/energy_dashboard.html
```

### 2. Click ⚙️ Configure Button
Fill in these 4 fields:

| Field | Example | Where to Find |
|-------|---------|---------------|
| **Home Assistant URL** | `http://homeassistant.local:8123` | Your HA instance URL |
| **API Token** | Long string starting with `eyJ0...` | Settings → Long-Lived Access Tokens → Create Token |
| **Solar Power Entity** | `sensor.fronius_p_ac` | Developer Tools → States → Search "power" or "solar" |
| **Battery SoC Entity** | `sensor.battery_soc` | Developer Tools → States → Search "battery" or "soc" |

### 3. Add Grid & Load (Optional)
```
Grid Power Entity:  sensor.grid_power  (negative=export)
House Load Entity:  sensor.house_load  (or calculate from others)
```

### 4. Click Save
Data loads instantly! ✅

---

## Finding Your Entity IDs

### Option A: Home Assistant UI (Easiest)
1. Go to **Developer Tools** → **States**
2. Search for keywords: `solar`, `battery`, `grid`, `load`, `power`
3. Look for sensors matching your hardware
4. Copy the entity ID (e.g., `sensor.fronius_p_ac`)

### Option B: Configuration YAML
Look in your integration configs:
```yaml
# Example from fronius integration
sensor:
  - platform: fronius
    # Auto-creates: sensor.fronius_p_ac, sensor.fronius_p_dc, etc.
```

### Option C: Create It (If Missing)
If your hardware doesn't expose a sensor, create a template sensor:

**House Load from components:**
```yaml
# Add to configuration.yaml
template:
  - sensor:
      - name: House Load
        unit_of_measurement: kW
        state: >
          {{ (
            states('sensor.grid_power') | float(0) -
            states('sensor.solar_power') | float(0) +
            states('sensor.battery_power') | float(0)
          ) | round(2) }}
```

Restart Home Assistant, then use `sensor.house_load` in the dashboard.

---

## Common Hardware Entity IDs

### Solar Inverters
| Hardware | Entity ID | Notes |
|----------|-----------|-------|
| Fronius | `sensor.fronius_p_ac` | Install Fronius integration |
| SolarEdge | `sensor.solaredge_current_power` | Requires API key |
| Huawei | `sensor.huawei_real_time_power` | Via Huawei Cloud integration |
| Victron | `sensor.victron_solar_power` | Via GX device |
| Solax | `sensor.solax_pv_power` | MQTT or direct API |

### Battery Systems
| Hardware | Entity ID | Notes |
|----------|-----------|-------|
| Tesla Powerwall | `sensor.powerwall_battery_percentage` | Via Tesla integration |
| Victron | `sensor.victron_battery_soc` | Via GX device |
| LiFePO4 | `sensor.battery_soc` | Via MQTT or CAN |
| Solax | `sensor.solax_battery_soc` | MQTT or direct API |

### Grid/Smart Meters
| Hardware | Entity ID | Notes |
|----------|-----------|-------|
| Shelly 3EM | `sensor.shelly_em_power` | Via Shelly integration |
| Smart Meter | `sensor.smart_meter_power` | Via your utility API |
| Sense | `sensor.sense_grid_power` | Via Sense app integration |
| Volkszahler | `sensor.volkszahler_power` | Via MQTT middleware |

### Pricing/Renewables
| Service | Entity ID | Setup |
|---------|-----------|-------|
| Amber Energy | `sensor.amber_price` | Install Amber integration |
| Octopus Energy | `sensor.octopus_electricity_rate` | Install Octopus integration |
| Tibber | `sensor.tibber_prices` | Install Tibber integration + webhook |
| Grid Renewables | `sensor.grid_renewables` | Via Amber or public API |

---

## Troubleshooting

### Dashboard shows "Configuring..." (not connecting)

**Problem**: Missing or wrong API token

**Solution**:
1. Go to **Settings → Long-Lived Access Tokens**
2. Create new token (copy the entire string)
3. Paste into Configure modal
4. Verify no extra spaces

---

### Gauges show "No data"

**Problem**: Entity ID doesn't exist

**Solution**:
1. Check Developer Tools → States
2. Search for your device name
3. Copy exact entity ID
4. Make sure entity has a numeric state value

---

### Data not updating (stuck on old values)

**Problem**: Sensor update interval is slow

**Solution**:
- Wait 5 seconds (dashboard polls every 5s)
- Check in HA if entity is updating: Developer Tools → States
- If HA entity is frozen, restart the integration

---

### "Unauthorized" error in console

**Problem**: Invalid API token

**Solution**:
- Generate new token: Settings → Long-Lived Access Tokens
- Must start with `eyJ0`
- Copy full string including end

---

## Advanced: URL Parameters

Skip the config modal with URL parameters:

```
energy_dashboard.html?
  ha_url=http://localhost:8123&
  ha_token=eyJ0...&
  solar_entity=sensor.solar_power&
  battery_soc_entity=sensor.battery_soc&
  grid_entity=sensor.grid_power&
  load_entity=sensor.house_load
```

## Advanced: Environment Variables (Docker)

If running in Docker/container:
```dockerfile
ENV HA_URL=http://homeassistant:8123
ENV HA_TOKEN=eyJ0...
```

The dashboard reads these automatically.

---

## Need More Help?

- **Full Guide**: See `INTEGRATION_GUIDE.md`
- **Feature Questions**: Check `IMPROVEMENTS_SUMMARY.md`
- **HA Integration Docs**: https://www.home-assistant.io/integrations/
- **Create Template Sensors**: https://www.home-assistant.io/integrations/template/

---

## Data Stored Locally

Your configuration is saved in **browser localStorage** - only on your device, never sent anywhere except to your Home Assistant instance.

To clear: `localStorage.clear()` in browser console (F12).

---

**That's it!** Your energy dashboard is now monitoring your system in real-time. 🚀
