"""DataUpdateCoordinator -- fetches all Voltiq data."""

from __future__ import annotations

import asyncio
import logging
import time
from datetime import timedelta, datetime, date
from typing import Any

import httpx
from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_BACKEND_URL, CONF_SUPABASE_URL, CONF_SUPABASE_KEY,
    CONF_RETAILER, CONF_AMBER_KEY,
    CONF_LV_KEY, CONF_LV_NMI, CONF_LV_PARTNER, CONF_AEMO_REGION,
    CONF_LATITUDE, CONF_LONGITUDE, CONF_SOLAR_CAPACITY,
    RETAILER_AMBER, RETAILER_LOCALVOLTS,
    DATA_PRICES, DATA_SYSTEM, DATA_EARNINGS,
    DATA_ALERTS, DATA_ADVISOR, DATA_SETTINGS, DATA_FORECAST,
    POLL_INTERVAL_PRICES,
)

_LOGGER = logging.getLogger(__name__)

AMBER_BASE = "https://api.amber.com.au/v1"


def _descriptor(p: float) -> str:
    if p < 0:
        return "negative"
    if p < 5:
        return "extremely_low"
    if p < 15:
        return "very_low"
    if p < 25:
        return "low"
    if p < 40:
        return "neutral"
    if p < 100:
        return "high"
    if p < 300:
        return "very_high"
    return "spike"


class VoltiqCoordinator(DataUpdateCoordinator):
    """Polls prices, device state, earnings, alerts, advisor tips, and solar forecast."""

    def __init__(self, hass: HomeAssistant, config: dict) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=DOMAIN,
            update_interval=timedelta(seconds=POLL_INTERVAL_PRICES),
        )
        self._cfg = config
        self._client = httpx.AsyncClient(timeout=10, follow_redirects=True)
        self._forecast_cache: dict = {}
        self._forecast_ts: float = 0.0

    async def _async_update_data(self) -> dict[str, Any]:
        prices, system, earnings, alerts, settings, forecast = await asyncio.gather(
            self._safe_fetch(self._fetch_prices, {}),
            self._safe_fetch(self._fetch_system, {"backend_online": False}),
            self._safe_fetch(self._fetch_earnings, {}),
            self._safe_fetch(self._fetch_alerts, {}),
            self._safe_fetch(self._fetch_settings, {}),
            self._safe_fetch(self._fetch_solar_forecast, {}),
        )
        advisor = await self._safe_fetch(
            lambda: self._fetch_advisor(system), {}
        )
        return {
            DATA_PRICES: prices,
            DATA_SYSTEM: system,
            DATA_EARNINGS: earnings,
            DATA_ALERTS: alerts,
            DATA_ADVISOR: advisor,
            DATA_SETTINGS: settings,
            DATA_FORECAST: forecast,
        }

    async def _safe_fetch(self, coro_fn, default):
        try:
            return await coro_fn()
        except Exception as exc:
            _LOGGER.debug("Fetch %s failed: %s", coro_fn.__name__, exc)
            return default

    # -- Supabase helpers --

    def _sb_hdrs(self) -> dict:
        key = self._cfg.get(CONF_SUPABASE_KEY, "")
        return {
            "apikey": key,
            "Authorization": f"Bearer {key}",
            "Accept": "application/json",
        }

    async def _sb_get(self, table: str, params: dict) -> list:
        url = self._cfg.get(CONF_SUPABASE_URL, "").rstrip("/")
        if not url:
            return []
        try:
            r = await self._client.get(
                f"{url}/rest/v1/{table}", headers=self._sb_hdrs(), params=params,
            )
            return r.json() if r.status_code == 200 else []
        except Exception as exc:
            _LOGGER.debug("sb_get %s: %s", table, exc)
            return []

    # -- Prices --

    async def _fetch_prices(self) -> dict:
        retailer = self._cfg.get(CONF_RETAILER, "aemo")
        try:
            if retailer == RETAILER_AMBER and self._cfg.get(CONF_AMBER_KEY):
                return await self._amber()
            if retailer == RETAILER_LOCALVOLTS and self._cfg.get(CONF_LV_KEY):
                return await self._localvolts()
        except Exception as exc:
            _LOGGER.warning("Price fetch (%s): %s -- falling back to AEMO", retailer, exc)
        return await self._aemo()

    async def _amber(self) -> dict:
        hdrs = {
            "Authorization": f"Bearer {self._cfg[CONF_AMBER_KEY]}",
            "Accept": "application/json",
        }
        r = await self._client.get(f"{AMBER_BASE}/sites", headers=hdrs)
        r.raise_for_status()
        sites = r.json()
        sid = sites[0]["id"] if sites else None
        if not sid:
            raise UpdateFailed("Amber: no sites found")
        r = await self._client.get(
            f"{AMBER_BASE}/sites/{sid}/prices/current",
            headers=hdrs,
            params={"next": 12, "previous": 2, "resolution": 5},
        )
        r.raise_for_status()
        data = r.json()
        cur = next(
            (d for d in data if d.get("type") == "CurrentInterval" and d.get("channelType") == "general"),
            None,
        )
        fi = next(
            (d for d in data if d.get("type") == "CurrentInterval" and d.get("channelType") == "feedIn"),
            None,
        )
        if not cur:
            raise UpdateFailed("Amber: no current interval")
        return {
            "import_price": cur.get("perKwh", 0),
            "feedin_price": fi.get("perKwh", 0) if fi else 0,
            "descriptor": cur.get("descriptor", "neutral"),
            "spike": cur.get("spikeStatus", "none") == "spike",
            "renewables": cur.get("renewables", 0),
            "source": "amber",
            "forecast_prices": [
                {
                    "start_time": d.get("startTime"),
                    "import_price": round(d.get("perKwh", 0), 2),
                    "descriptor": d.get("descriptor", "neutral"),
                }
                for d in data
                if d.get("type") == "ForecastInterval" and d.get("channelType") == "general"
            ],
        }

    async def _localvolts(self) -> dict:
        nmi = self._cfg.get(CONF_LV_NMI, "")
        partner = self._cfg.get(CONF_LV_PARTNER, "")
        hdrs = {"Authorization": f"Bearer {self._cfg[CONF_LV_KEY]}:{partner}"}
        r = await self._client.get(
            f"https://api.localvolts.com/v1/customer/interval?NMI={nmi}", headers=hdrs,
        )
        r.raise_for_status()
        d = r.json()[0]
        ip = float(d.get("costsFlexUp", 0)) * 100
        fip = float(d.get("earningsFlexUp", 0)) * 100
        return {
            "import_price": round(ip, 2),
            "feedin_price": round(fip, 2),
            "descriptor": _descriptor(ip),
            "spike": ip > 300,
            "renewables": 0,
            "source": "localvolts",
            "forecast_prices": [],
        }

    async def _aemo(self) -> dict:
        region = self._cfg.get(CONF_AEMO_REGION, "NSW1")
        try:
            r = await self._client.get(
                "https://visualisations.aemo.com.au/aemo/apps/api/report/5MIN",
            )
            if r.status_code == 200 and r.text.strip():
                row = next(
                    (d for d in r.json().get("5MIN", []) if d.get("REGIONID") == region),
                    None,
                )
                if row:
                    spot = float(row.get("RRP", 0)) / 10
                    ip = round(spot + 10, 2)
                    fip = round(spot * 0.92, 2)
                    return {
                        "import_price": ip,
                        "feedin_price": fip,
                        "descriptor": _descriptor(ip),
                        "spike": ip > 300,
                        "renewables": 45,
                        "source": "aemo",
                        "forecast_prices": [],
                    }
        except Exception as exc:
            _LOGGER.debug("AEMO primary: %s", exc)
        # OpenNEM fallback
        try:
            nem = region.rstrip("1")
            r = await self._client.get(
                f"https://api.opennem.org.au/stats/price/NEM/{nem}/",
            )
            series = r.json().get("data", [{}])[0].get("history", {})
            rrp = next(
                (v for v in reversed(series.get("data", [])) if v is not None),
                None,
            )
            if rrp is not None:
                spot = float(rrp)
                ip = round(spot / 10 + 10, 2)
                fip = round(spot / 10 * 0.92, 2)
                return {
                    "import_price": ip,
                    "feedin_price": fip,
                    "descriptor": _descriptor(ip),
                    "spike": ip > 300,
                    "renewables": 45,
                    "source": "aemo_opennem",
                    "forecast_prices": [],
                }
        except Exception as exc:
            _LOGGER.warning("AEMO fallback: %s", exc)
        return {
            "import_price": 0,
            "feedin_price": 0,
            "descriptor": "unknown",
            "spike": False,
            "renewables": 0,
            "source": "unavailable",
            "forecast_prices": [],
        }

    # -- System state --

    async def _fetch_system(self) -> dict:
        backend = self._cfg.get(CONF_BACKEND_URL, "").rstrip("/")
        if backend:
            try:
                r = await self._client.get(f"{backend}/api/state", timeout=6)
                if r.status_code == 200:
                    data = r.json()
                    data["backend_online"] = True
                    return data
                r2 = await self._client.get(f"{backend}/api/health", timeout=4)
                if r2.status_code == 200:
                    return {"backend_online": True}
            except Exception:
                pass
        rows = await self._sb_get("system_state", {"order": "updated_at.desc", "limit": "1"})
        if rows:
            return {**rows[0], "backend_online": bool(backend)}
        return {"backend_online": False}

    # -- Earnings --

    async def _fetch_earnings(self) -> dict:
        today = date.today().isoformat()
        rows = await self._sb_get("earnings", {"date": f"eq.{today}", "limit": "1"})
        today_data = rows[0] if rows else {}

        week_rows = await self._sb_get("earnings", {
            "order": "date.desc",
            "limit": "7",
            "select": "earned_dollars,cost_dollars,solar_kwh,exported_kwh",
        })
        weekly_net = sum(
            float(r.get("earned_dollars", 0)) - float(r.get("cost_dollars", 0))
            for r in week_rows
        )
        earned = float(today_data.get("earned_dollars", 0))
        cost = float(today_data.get("cost_dollars", 0))
        return {
            "earned_today": earned,
            "cost_today": cost,
            "net_today": round(earned - cost, 4),
            "solar_kwh_today": float(today_data.get("solar_kwh", 0)),
            "exported_kwh": float(today_data.get("exported_kwh", 0)),
            "imported_kwh": float(today_data.get("imported_kwh", 0)),
            "weekly_net": round(weekly_net, 2),
        }

    # -- Alerts --

    async def _fetch_alerts(self) -> dict:
        rows = await self._sb_get("alerts", {"order": "created_at.desc", "limit": "10"})
        latest = rows[0] if rows else {}
        return {
            "count": len(rows),
            "latest": latest.get("message", ""),
            "latest_level": latest.get("level", ""),
            "items": rows[:5],
        }

    # -- Advisor tips --

    async def _fetch_advisor(self, system: dict) -> dict:
        tips = system.get("advisor_tips") or []
        if isinstance(tips, list) and tips:
            return {"tips": tips, "latest_tip": tips[0]}

        prices = (self.data or {}).get(DATA_PRICES, {})
        ip = float(prices.get("import_price", 0))
        fip = float(prices.get("feedin_price", 0))
        soc = float(system.get("soc", 50))
        if ip < 0 and soc < 90:
            tip = f"Import price NEGATIVE ({ip:.1f}c) -- great time to charge battery!"
        elif ip >= 300 and soc > 20:
            tip = f"PRICE SPIKE ({ip:.1f}c) -- discharge battery now."
        elif fip < 0:
            tip = f"Feed-in is negative ({fip:.1f}c) -- stop exporting, use battery."
        else:
            tip = f"System balanced -- {ip:.1f}c import, {fip:.1f}c feed-in, {soc:.0f}% SoC."
        return {"tips": [tip], "latest_tip": tip}

    # -- Settings --

    async def _fetch_settings(self) -> dict:
        rows = await self._sb_get("settings", {
            "select": "min_soc,max_soc,reserve_soc,poll_interval,charge_below_import,discharge_above_fit",
            "limit": "1",
        })
        return rows[0] if rows else {}

    # -- Solar forecast (Open-Meteo, 30-min cache) --

    async def _fetch_solar_forecast(self) -> dict:
        if time.monotonic() - self._forecast_ts < 1800 and self._forecast_cache:
            return self._forecast_cache
        lat = self._cfg.get(CONF_LATITUDE)
        lon = self._cfg.get(CONF_LONGITUDE)
        capacity = float(self._cfg.get(CONF_SOLAR_CAPACITY, 6.6))
        if not lat or not lon:
            return {}
        r = await self._client.get(
            "https://api.open-meteo.com/v1/forecast",
            params={
                "latitude": lat,
                "longitude": lon,
                "hourly": "direct_radiation,diffuse_radiation,cloud_cover,temperature_2m",
                "daily": "sunrise,sunset,uv_index_max,precipitation_sum",
                "timezone": "auto",
                "forecast_days": 3,
            },
        )
        r.raise_for_status()
        d = r.json()
        hourly = d.get("hourly", {})
        times = hourly.get("time", [])
        direct = hourly.get("direct_radiation", [])
        diff_r = hourly.get("diffuse_radiation", [])
        cloud = hourly.get("cloud_cover", [])
        temp = hourly.get("temperature_2m", [])
        today_date = date.today()
        hours: list[dict] = []
        today_kwh = tomorrow_kwh = day2_kwh = 0.0
        for i, t in enumerate(times):
            dt = datetime.fromisoformat(t)
            ghi = (direct[i] if i < len(direct) else 0) + (diff_r[i] if i < len(diff_r) else 0)
            est_kw = round(ghi * 0.0008 * capacity, 2)
            hours.append({
                "time": t,
                "ghi_wm2": round(ghi, 1),
                "estimated_kw": est_kw,
                "cloud_cover": cloud[i] if i < len(cloud) else 0,
                "temperature": temp[i] if i < len(temp) else 0,
            })
            day_offset = (dt.date() - today_date).days
            if day_offset == 0:
                today_kwh += est_kw
            elif day_offset == 1:
                tomorrow_kwh += est_kw
            elif day_offset == 2:
                day2_kwh += est_kw
        result = {
            "hours": hours,
            "today_kwh": round(today_kwh, 1),
            "tomorrow_kwh": round(tomorrow_kwh, 1),
            "day2_kwh": round(day2_kwh, 1),
            "daily": d.get("daily", {}),
            "timezone": d.get("timezone", ""),
        }
        self._forecast_cache = result
        self._forecast_ts = time.monotonic()
        return result

    # -- Controls --

    async def set_battery_mode(self, mode: str, power: int = 0) -> bool:
        backend = self._cfg.get(CONF_BACKEND_URL, "").rstrip("/")
        if not backend:
            return False
        try:
            r = await self._client.post(
                f"{backend}/api/control",
                json={"device": "neovolt", "command": mode, "power": power},
            )
            return r.status_code == 200 and r.json().get("ok")
        except Exception as exc:
            _LOGGER.error("set_battery_mode: %s", exc)
            return False

    async def update_setting(self, key: str, value: Any) -> bool:
        sb_url = self._cfg.get(CONF_SUPABASE_URL, "").rstrip("/")
        key_hdr = self._cfg.get(CONF_SUPABASE_KEY, "")
        if not sb_url or not key_hdr:
            return False
        try:
            hdrs = {
                **self._sb_hdrs(),
                "Prefer": "resolution=merge-duplicates,return=minimal",
            }
            r = await self._client.patch(
                f"{sb_url}/rest/v1/settings?limit=1",
                headers=hdrs,
                json={key: value, "updated_at": datetime.now().isoformat()},
            )
            return r.status_code in (200, 204)
        except Exception as exc:
            _LOGGER.error("update_setting %s: %s", key, exc)
            return False

    async def async_shutdown(self) -> None:
        await self._client.aclose()
        await super().async_shutdown()
