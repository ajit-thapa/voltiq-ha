# Voltiq Energy Manager

[![HACS](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz)
[![GitHub Release](https://img.shields.io/github/v/release/ajit-thapa/voltiq-ha)](https://github.com/ajit-thapa/voltiq-ha/releases)

A Home Assistant integration for Australian energy management. Real-time electricity prices, solar forecasting, battery control, and earnings tracking in one place.

## Features

- **Live electricity prices** from AEMO spot market, Amber Electric, or Localvolts
- **Solar forecast** via Open-Meteo (free, no API key)
- **Battery control** -- force charge, force discharge, self-consume, hold SoC
- **Earnings tracking** -- daily/weekly earnings, costs, net profit (via Supabase)
- **Auto-generated dashboard** -- 5-view Lovelace dashboard added to your sidebar
- **Sensor mapping** -- use your own solar/battery/grid sensors from any integration
- **Alerts & advisor** -- price spike warnings and rule-based dispatch tips

## Installation

### HACS (recommended)

1. Open HACS in Home Assistant
2. Click the three dots menu > **Custom repositories**
3. Add `https://github.com/ajit-thapa/voltiq-ha` as an **Integration**
4. Search for "Voltiq" and install
5. Restart Home Assistant
6. Go to **Settings > Integrations > Add Integration > Voltiq Energy Manager**

### Manual

1. Copy `custom_components/voltiq/` to your `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration via **Settings > Integrations**

## Setup

The config flow walks you through:

1. **Retailer** -- choose AEMO (free), Amber Electric, or Localvolts
2. **Supabase** (optional) -- connect for earnings, alerts, and settings sync
3. **Solar forecast** -- enter your location and system capacity
4. **Sensor mapping** (optional) -- map your existing HA sensors (SolarEdge, Enphase, Tesla, etc.)

### Options

After setup, go to **Settings > Integrations > Voltiq > Configure** to:

- Map external sensors (solar PV, battery SoC, grid power, energy meters, price sensors)
- Toggle the auto-generated sidebar dashboard
- Update backend URL, Supabase credentials, or solar capacity

## Entities

### Sensors
| Entity | Description |
|--------|-------------|
| Import Price | Current electricity import price (c/kWh) |
| Feed-in Price | Current feed-in tariff (c/kWh) |
| Price Level | Descriptor: negative, low, neutral, high, spike |
| Battery SoC | Battery state of charge (%) |
| Solar Power | Current solar generation (kW) |
| Battery Power | Battery charge/discharge power (kW) |
| Grid Power | Grid import/export power (kW) |
| Home Load | House consumption (kW) |
| Solar Forecast Today | Estimated solar generation today (kWh) |
| Earned/Cost/Net Today | Daily earnings tracking (AUD) |
| Advisor Tip | Smart dispatch recommendation |

### Controls
| Entity | Description |
|--------|-------------|
| Battery Mode (select) | Self Consumption, Max Export, Force Charge, Force Discharge, Hold SoC |
| Min/Max Battery SoC (number) | Adjustable SoC limits |
| Force Charge/Discharge/Self Consume (button) | Quick battery actions |

### Binary Sensors
| Entity | Description |
|--------|-------------|
| Backend Online | Voltiq backend connectivity |
| Price Spike | True when import price exceeds spike threshold |

## Dashboard

When enabled (default), a **Voltiq Energy** dashboard appears in your sidebar with five views:

- **Overview** -- prices, power flow, battery gauge, forecast, advisor, earnings
- **Battery** -- SoC history, health details, controls
- **Solar** -- production graphs, forecast, inverter status
- **Energy & Costs** -- earnings, energy statistics, price history
- **Settings** -- battery controls, system info

## Supported Retailers

| Retailer | API Key Required | Data |
|----------|-----------------|------|
| AEMO Spot | No | 5-min spot price by region |
| Amber Electric | Yes | Real-time price, forecast, spike status, renewables |
| Localvolts | Yes | Interval pricing per NMI |

## Requirements

- Home Assistant 2024.1.0+
- For battery control: Voltiq backend running locally
- For earnings/alerts: Supabase project with Voltiq schema

## License

MIT
