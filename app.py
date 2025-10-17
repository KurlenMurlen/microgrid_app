from flask import Flask, render_template, jsonify, request, Response, stream_with_context
from flask import send_file
import sqlite3, pandas as pd, joblib, json, os, socket, time
from typing import Optional
import requests
from datetime import timedelta
import numpy as np
from sklearn.linear_model import LinearRegression, Ridge, Lasso

app = Flask(__name__, template_folder="templates")
MODEL = joblib.load("models/model.joblib")
with open("models/metrics.json","r") as f:
    METRICS = json.load(f)

DB_PATH = "data/consumption.db"
VOSK_MODEL_URL = os.environ.get(
    "VOSK_MODEL_PT_URL",
    "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip",
)
VOSK_LOCAL_PATH = os.path.join("models", "vosk-model-small-pt-0.3.zip")

def _ensure_dir(p: str):
    d = os.path.dirname(p)
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)

def compute_drift(df: pd.DataFrame) -> dict:
    """Simple drift detection comparing last 24h vs previous 24h mean and variance.
    Returns: { change_pct, z, level } level in {'low','warn','high'}
    """
    try:
        s = df.copy().sort_values("timestamp")
        s["timestamp"] = pd.to_datetime(s["timestamp"]).dt.tz_localize(None)
        if len(s) < 48:
            return {"change_pct": 0.0, "z": 0.0, "level": "low"}
        if len(s) >= 2:
            dt_hours = float(pd.Series(s["timestamp"]).diff().dropna().dt.total_seconds().median() / 3600.0)
            if not np.isfinite(dt_hours) or dt_hours <= 0:
                dt_hours = 1.0
        else:
            dt_hours = 1.0
        steps_day = int(max(1, round(24.0 / dt_hours)))
        last24 = s.tail(steps_day)
        prev24 = s.tail(steps_day * 2).head(steps_day)
        c1 = last24["consumption_kW"].astype(float).to_numpy()
        c0 = prev24["consumption_kW"].astype(float).to_numpy()
        m1 = float(np.mean(c1))
        m0 = float(np.mean(c0))
        v1 = float(np.var(c1, ddof=1) if len(c1) > 1 else 0.0)
        v0 = float(np.var(c0, ddof=1) if len(c0) > 1 else 0.0)
        change_pct = 0.0 if m0 == 0 else (m1 - m0) / m0 * 100.0
        n = float(steps_day)
        pooled_var = ((n - 1) * v0 + (n - 1) * v1) / max(1.0, (2 * n - 2))
        pooled_std = float(np.sqrt(max(1e-9, pooled_var)))
        z = 0.0 if pooled_std == 0 else (m1 - m0) / (pooled_std / np.sqrt(n))
        level = "low"
        if abs(change_pct) >= 20 or abs(z) >= 2.5:
            level = "high"
        elif abs(change_pct) >= 10 or abs(z) >= 1.8:
            level = "warn"
        return {"change_pct": round(change_pct, 2), "z": round(z, 2), "level": level}
    except Exception:
        return {"change_pct": 0.0, "z": 0.0, "level": "low"}

@app.route("/api/vosk/model")
def api_vosk_model():
    """Serve the Vosk PT-BR model from local cache. If missing, download once and cache.
    Hardening: retries with backoff, temp file + atomic rename, larger timeout and chunk size,
    and cache-friendly headers. Same-origin to avoid CORS."""
    try:
        if not os.path.exists(VOSK_LOCAL_PATH):
            _ensure_dir(VOSK_LOCAL_PATH)
            tmp_path = VOSK_LOCAL_PATH + ".part"
            # Retry loop
            attempts = 0
            last_err = None
            while attempts < 3:
                attempts += 1
                try:
                    with requests.get(VOSK_MODEL_URL, stream=True, timeout=120) as r:
                        r.raise_for_status()
                        with open(tmp_path, "wb") as f:
                            for chunk in r.iter_content(chunk_size=1024 * 1024):  # 1MB
                                if chunk:
                                    f.write(chunk)
                    # Atomic replace
                    os.replace(tmp_path, VOSK_LOCAL_PATH)
                    break
                except Exception as e:
                    last_err = e
                    # Clean partial
                    try:
                        if os.path.exists(tmp_path):
                            os.remove(tmp_path)
                    except Exception:
                        pass
                    # Backoff
                    time.sleep(1.5 * attempts)
            if not os.path.exists(VOSK_LOCAL_PATH):
                raise RuntimeError(f"Download falhou após {attempts} tentativas: {last_err}")
        # Serve cached file with cache headers
        resp = send_file(VOSK_LOCAL_PATH, mimetype="application/zip", as_attachment=False, conditional=True)
        try:
            mtime = os.path.getmtime(VOSK_LOCAL_PATH)
            size = os.path.getsize(VOSK_LOCAL_PATH)
            resp.headers['Cache-Control'] = 'public, max-age=2592000, immutable'  # 30 days
            resp.headers['Content-Length'] = str(size)
            resp.headers['Last-Modified'] = time.strftime('%a, %d %b %Y %H:%M:%S GMT', time.gmtime(mtime))
        except Exception:
            pass
        return resp
    except Exception as e:
        return jsonify({"error": "failed_to_fetch_model", "detail": str(e)}), 500

@app.route("/api/vosk/status")
def api_vosk_status():
    """Return JSON with cache status for the Vosk model zip."""
    try:
        exists = os.path.exists(VOSK_LOCAL_PATH)
        size = os.path.getsize(VOSK_LOCAL_PATH) if exists else 0
        mtime = os.path.getmtime(VOSK_LOCAL_PATH) if exists else None
        return jsonify({
            "exists": exists,
            "size": int(size),
            "mtime": (None if mtime is None else int(mtime)),
            "source_url": VOSK_MODEL_URL,
            "local_path": VOSK_LOCAL_PATH,
        })
    except Exception as e:
        return jsonify({"exists": False, "error": str(e)}), 200

def load_source(source: str = "db"):
    source = (source or "db").lower()
    if source == "csv":
        # Expecting columns: timestamp, consumption_kW, temperature_C
        df = pd.read_csv("data/synthetic_consumption.csv")
        if "timestamp" in df.columns:
            df["timestamp"] = pd.to_datetime(df["timestamp"])
        else:
            # Fallback: create a monotonic timestamp if missing
            df.insert(0, "timestamp", pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq="H"))
        if "consumption_kW" not in df.columns:
            # Try common alternatives
            for alt in ["consumption", "load", "power_kW"]:
                if alt in df.columns:
                    df = df.rename(columns={alt: "consumption_kW"})
                    break
        if "temperature_C" not in df.columns:
            # Derive a mild diurnal temperature cycle if not provided
            hours = df["timestamp"].dt.hour
            df["temperature_C"] = 24 + 3 * np.sin((hours - 6) / 24 * 2 * np.pi)
        return df[["timestamp", "consumption_kW", "temperature_C"]].sort_values("timestamp")
    # default: DB
    return load_latest_data()

def load_latest_data():
    """Load data from SQLite; on failure or empty, fall back to CSV or generate synthetic."""
    try:
        conn = sqlite3.connect(DB_PATH)
        df = pd.read_sql_query(
            "SELECT timestamp, consumption_kW, temperature_C FROM consumption ORDER BY timestamp ASC",
            conn,
            parse_dates=["timestamp"],
        )
        conn.close()
        if df is not None and len(df):
            return df
    except Exception:
        pass
    # Fallback to CSV if available
    try:
        csv_path = os.path.join("data", "synthetic_consumption.csv")
        if os.path.exists(csv_path):
            df = pd.read_csv(csv_path)
            if "timestamp" in df.columns:
                df["timestamp"] = pd.to_datetime(df["timestamp"])
            else:
                df.insert(0, "timestamp", pd.date_range(end=pd.Timestamp.now(), periods=len(df), freq="H"))
            if "consumption_kW" not in df.columns:
                for alt in ["consumption", "load", "power_kW"]:
                    if alt in df.columns:
                        df = df.rename(columns={alt: "consumption_kW"})
                        break
            if "temperature_C" not in df.columns:
                hours = pd.to_datetime(df["timestamp"]).dt.hour
                df["temperature_C"] = 24 + 3 * np.sin((hours - 6) / 24 * 2 * np.pi)
            return df[["timestamp", "consumption_kW", "temperature_C"]].sort_values("timestamp")
    except Exception:
        pass
    # Final fallback: generate synthetic for the last ~14 days hourly
    now = pd.Timestamp.now().tz_localize(None)
    idx = pd.date_range(end=now, periods=24 * 14, freq="H")
    hours = idx.hour + idx.minute / 60
    temp = 24 + 3 * np.sin((hours - 6) / 24 * 2 * np.pi)
    base = 2.5 + 0.8 * (1 + np.sin((hours - 6) / 24 * 2 * np.pi)) + 0.2 * np.sin((hours) / 24 * 4 * np.pi)
    noise = np.random.normal(0, 0.08, size=len(idx))
    load = np.maximum(0.2, (base + 0.05 * (temp - 24) + noise))
    return pd.DataFrame({"timestamp": idx, "consumption_kW": load, "temperature_C": temp})

def estimate_temp(ts: pd.Timestamp) -> float:
    ts = pd.to_datetime(ts)
    hour = ts.hour + (ts.minute or 0)/60
    return float(24 + 3 * np.sin((hour - 6) / 24 * 2 * np.pi))

def _weather_forecast(ts: pd.Timestamp) -> Optional[float]:
    """Optional external weather forecast for a given timestamp. Expected WEATHER_API_URL that returns
    JSON containing forecast entries with 'timestamp' and 'temperature_C'. This is a best-effort helper; returns None on any issue."""
    url = os.environ.get("WEATHER_API_URL")
    if not url:
        return None
    try:
        r = requests.get(url, timeout=4)
        r.raise_for_status()
        j = r.json()
        items = j.get("forecast") or j
        target = pd.to_datetime(ts)
        # pick the closest entry
        best = None
        best_dt = None
        for it in items:
            t = pd.to_datetime(it.get("timestamp"))
            if pd.isna(t):
                continue
            if best is None or abs((t - target).total_seconds()) < abs((best_dt - target).total_seconds()):
                best = float(it.get("temperature_C", np.nan))
                best_dt = t
        if best is not None and np.isfinite(best):
            return best
    except Exception:
        return None
    return None

def make_lag_features(df, n_lags=24):
    df = df.copy().sort_values("timestamp")
    for lag in range(1, n_lags+1):
        df[f"lag_{lag}"] = df["consumption_kW"].shift(lag)
    df["hour"] = df["timestamp"].dt.hour
    df["dayofweek"] = df["timestamp"].dt.dayofweek
    df = df.dropna().reset_index(drop=True)
    return df

def compute_kpis(df: pd.DataFrame):
    df = df.copy().sort_values("timestamp")
    last = df.iloc[-1]
    window = df.tail(24)
    return {
        "last_updated": pd.to_datetime(last["timestamp"]).isoformat(),
        "current_load_kw": float(last["consumption_kW"]),
        "avg_24h_kw": float(window["consumption_kW"].mean()) if len(window) else None,
        "peak_24h_kw": float(window["consumption_kW"].max()) if len(window) else None,
        "current_temp_c": float(last["temperature_C"]) if "temperature_C" in df.columns else None,
    }

def estimate_pv_kw(ts: pd.Timestamp, temp_c: Optional[float] = None, pv_factor: float = 1.0):
    # Simple diurnal PV profile peaking at midday
    hour = ts.hour
    pv_peak = 3.0  # kW, illustrative
    # sine from 6h to 18h
    x = max(0.0, np.sin(np.pi * (hour - 6) / 12))
    pv = pv_peak * x * float(pv_factor)
    if temp_c is not None:
        # very light derate in high temp (illustrative)
        pv *= 1.0 - max(0.0, (temp_c - 30)) * 0.005
    return max(0.0, float(pv))

def compute_equipment_state(df: pd.DataFrame, *, pv_factor: float = 1.0, batt_power_limit_kw: float = 2.0, soc_init_pct: float = 50.0):
    """Compute simple PV/battery/grid flows for the latest step using a timestep-aware battery model.
    - battery_kw: positive = descarregando para a carga; negativo = carregando
    """
    if df is None or len(df) == 0:
        return {"pv_kw": 0.0, "load_kw": 0.0, "grid_kw": 0.0, "battery_kw": 0.0, "battery_soc": 50}
    df = df.copy().sort_values("timestamp")
    df["timestamp"] = pd.to_datetime(df["timestamp"]).dt.tz_localize(None)
    # Determine timestep in hours (median of diffs); fallback to 1h
    if len(df) >= 2:
        dt_hours = float(pd.Series(df["timestamp"]).diff().dropna().dt.total_seconds().median() / 3600.0)
        if not np.isfinite(dt_hours) or dt_hours <= 0:
            dt_hours = 1.0
    else:
        dt_hours = 1.0
    # Use up to last 24 hours of history
    steps = int(max(1, round(24.0 / dt_hours)))
    recent = df.tail(steps).reset_index(drop=True)
    # Estimate PV for each timestamp
    temps = recent["temperature_C"] if "temperature_C" in recent.columns else [None] * len(recent)
    recent["pv_kw"] = [estimate_pv_kw(ts, (float(t) if t is not None else None), pv_factor=pv_factor) for ts, t in zip(recent["timestamp"], temps)]
    load = recent["consumption_kW"].astype(float).to_numpy()
    pv = recent["pv_kw"].astype(float).to_numpy()
    # Battery model
    cap_kwh = 10.0
    soc = float(np.clip(soc_init_pct, 0, 100)) / 100.0 * cap_kwh
    soc_hist = []
    batt_kw_hist = []  # + discharge to load, - charge
    batt_power_limit = float(max(0.0, batt_power_limit_kw))  # kW limit
    for l, p in zip(load, pv):
        net = l - p  # positive => falta energia; negative => sobra de PV
        if net > 0 and soc > 0:
            # discharge limited by power and available energy for this dt
            max_discharge_kw = soc / dt_hours
            discharge_kw = float(min(net, batt_power_limit, max_discharge_kw))
            soc -= discharge_kw * dt_hours
            batt_kw_hist.append(discharge_kw)
        elif net < 0 and soc < cap_kwh:
            # charge limited by power and free capacity for this dt
            surplus_kw = -net
            max_charge_kw = (cap_kwh - soc) / dt_hours
            charge_kw = float(min(surplus_kw, batt_power_limit, max_charge_kw))
            soc += charge_kw * dt_hours
            batt_kw_hist.append(-charge_kw)
        else:
            batt_kw_hist.append(0.0)
        soc_hist.append(soc)
    last_load = float(load[-1])
    last_pv = float(pv[-1])
    last_batt_kw = float(batt_kw_hist[-1])
    grid_kw = max(0.0, last_load - last_pv - last_batt_kw)
    return {
        "pv_kw": round(last_pv, 3),
        "load_kw": round(last_load, 3),
        "battery_kw": round(last_batt_kw, 3),
        "grid_kw": round(grid_kw, 3),
        "battery_soc": int(round(100 * soc / cap_kwh)),
    }

def compute_alerts(kpis: dict, equipment: dict) -> list:
    """Return a list of alert dicts: {level: 'info'|'warn'|'crit', message: str}"""
    alerts = []
    try:
        soc = equipment.get("battery_soc")
        grid = equipment.get("grid_kw") or 0.0
        load = kpis.get("current_load_kw") or 0.0
        avg = kpis.get("avg_24h_kw")
        peak = kpis.get("peak_24h_kw")
        if soc is not None and soc < 15:
            alerts.append({"level": "warn", "message": f"Bateria baixa: SOC {soc}%"})
        if avg is not None and load > avg * 1.2:
            alerts.append({"level": "info", "message": f"Carga alta vs média 24h ({load:.2f} kW)"})
        if peak is not None and load >= peak * 0.95:
            alerts.append({"level": "warn", "message": "Próximo do pico das últimas 24h"})
        if grid > (avg or grid) * 0.8:
            alerts.append({"level": "info", "message": f"Uso elevado da rede ({grid:.2f} kW)"})
    except Exception:
        pass
    return alerts

def _ensure_live_table():
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "CREATE TABLE IF NOT EXISTS live_ticks (timestamp TEXT PRIMARY KEY, consumption_kW REAL, temperature_C REAL)"
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def _insert_live_point(point: dict):
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute(
            "INSERT OR REPLACE INTO live_ticks (timestamp, consumption_kW, temperature_C) VALUES (?, ?, ?)",
            (pd.to_datetime(point["timestamp"]).isoformat(), float(point["consumption_kW"]), float(point.get("temperature_C", 24.0)))
        )
        conn.commit()
        conn.close()
    except Exception:
        pass

def generate_context(kpis: dict, equipment: dict) -> str:
    load = kpis.get("current_load_kw")
    avg = kpis.get("avg_24h_kw")
    peak = kpis.get("peak_24h_kw")
    temp = kpis.get("current_temp_c")
    pv = equipment.get("pv_kw")
    grid = equipment.get("grid_kw")
    batt = equipment.get("battery_kw")
    soc = equipment.get("battery_soc")
    parts = []
    if load is not None and avg is not None:
        trend = "acima" if load > avg * 1.05 else ("abaixo" if load < avg * 0.95 else "em linha com")
        parts.append(f"Carga atual {load:.2f} kW, {trend} da média das últimas 24h ({avg:.2f} kW).")
    if peak is not None:
        parts.append(f"Pico 24h: {peak:.2f} kW.")
    if temp is not None:
        parts.append(f"Temperatura ambiente: {temp:.1f} °C.")
    parts.append(f"PV entrega {pv:.2f} kW.")
    if batt is not None:
        if batt > 0:
            parts.append(f"Bateria descarregando {batt:.2f} kW (SOC {soc}%).")
        elif batt < 0:
            parts.append(f"Bateria carregando {abs(batt):.2f} kW (SOC {soc}%).")
        else:
            parts.append(f"Bateria em repouso (SOC {soc}%).")
    parts.append(f"Consumo da rede: {grid:.2f} kW.")
    # Quick qualitative status
    status = "estável"
    if grid and grid > (avg or grid) * 0.7:
        status = "alto uso da rede"
    elif pv and pv > (load or pv) * 0.6:
        status = "alta penetração solar"
    parts.append(f"Estado geral: {status}.")
    return " ".join(parts)

def _live_external_point() -> Optional[dict]:
    """Optionally fetch a live point from external API if configured.
    Expected LIVE_API_URL returning JSON with keys: timestamp, consumption_kW, temperature_C
    """
    url = os.environ.get("LIVE_API_URL")
    if not url:
        return None
    headers = {}
    if os.environ.get("LIVE_API_TOKEN"):
        headers["Authorization"] = f"Bearer {os.environ['LIVE_API_TOKEN']}"
    try:
        r = requests.get(url, headers=headers, timeout=5)
        r.raise_for_status()
        j = r.json()
        ts = pd.to_datetime(j.get("timestamp", pd.Timestamp.utcnow()))
        return {
            "timestamp": ts,
            "consumption_kW": float(j.get("consumption_kW", 0.0)),
            "temperature_C": float(j.get("temperature_C", 24.0)),
        }
    except Exception:
        return None

def _simulate_next_point(ts: pd.Timestamp, load: float, temp: float, factor: float = 1.0) -> dict:
    ts = (pd.to_datetime(ts) + pd.Timedelta(minutes=1)).tz_localize(None)
    hour = ts.hour + ts.minute/60
    base = 2.5 + 0.8 * (1 + np.sin((hour-6)/24*2*np.pi))  # diurnal base
    temp_next = 24 + 3*np.sin((hour-6)/24*2*np.pi)
    noise = np.random.normal(0, 0.05)
    load_next = max(0.2, (base + 0.05*(temp_next-24) + noise) * float(factor))
    return {"timestamp": ts, "consumption_kW": float(load_next), "temperature_C": float(temp_next)}

def detect_anomalies(df: pd.DataFrame) -> list:
    """Very simple anomaly detection using rolling z-score on consumption over a 24h window.
    Returns a list of dicts with timestamp and value for anomalies."""
    if df is None or len(df) < 10:
        return []
    s = df.sort_values("timestamp").copy()
    s["consumption_kW"] = s["consumption_kW"].astype(float)
    # estimate dt to choose window size ~24h
    if len(s) >= 2:
        dt_hours = float(pd.Series(s["timestamp"]).diff().dropna().dt.total_seconds().median() / 3600.0)
        if not np.isfinite(dt_hours) or dt_hours <= 0:
            dt_hours = 1.0
    else:
        dt_hours = 1.0
    window = int(max(5, round(24.0 / dt_hours)))
    s["roll_mean"] = s["consumption_kW"].rolling(window=window, min_periods=5).mean()
    s["roll_std"] = s["consumption_kW"].rolling(window=window, min_periods=5).std().replace(0, np.nan)
    s["z"] = (s["consumption_kW"] - s["roll_mean"]) / s["roll_std"]
    out = s[(s["z"].abs() >= 3) & s["z"].notna()].tail(50)
    return [{"x": pd.to_datetime(r["timestamp"]).isoformat(), "y": float(r["consumption_kW"]), "text": f"z={float(r['z']):.2f}" } for _, r in out.iterrows()]

def optimize_battery(preds: list, pv_factor: float = 1.0, batt_limit_kw: float = 2.0, soc_init_pct: float = 50.0, cap_kwh: float = 10.0) -> dict:
    """Greedy heuristic using TOU: descarrega em tarifa alta, carrega em baixa e com excedente de PV.
    Returns summary and per-step plan over forecast horizon.
    preds: list of {ts(str), y(load_kW)} length ~24
    """
    if not preds:
        return {"baseline_cost": 0.0, "optimized_cost": 0.0, "savings": 0.0, "plan": []}
    plan = []
    soc = float(np.clip(soc_init_pct, 0, 100)) / 100.0 * cap_kwh
    for p in preds:
        ts = pd.to_datetime(p["ts"]) if isinstance(p["ts"], str) else p["ts"]
        load = max(0.0, float(p["y"]))
        temp_f = _weather_forecast(ts) or estimate_temp(ts)
        pv = estimate_pv_kw(ts, temp_f, pv_factor=pv_factor)
        net = max(0.0, load - pv)  # demanda para rede antes da bateria
        rate = tariff_rate(ts)
        batt = 0.0
        dt = 1.0  # horas por passo de forecast
        max_discharge_kw = soc / dt
        max_charge_kw = (cap_kwh - soc) / dt
        if rate >= 1.0 and net > 0 and soc > 0:
            # descarregar em horário caro
            batt = float(min(net, batt_limit_kw, max_discharge_kw))
            soc = max(0.0, soc - batt * dt)
        elif rate <= 0.6 and soc < cap_kwh:
            # carregar em horário barato (da rede)
            charge = float(min(batt_limit_kw, max_charge_kw))
            batt = -charge
            soc = min(cap_kwh, soc + charge * dt)
        # baseline/optimized grid
        grid_base = net
        grid_opt = max(0.0, net - batt)
        plan.append({
            "ts": ts.isoformat(),
            "load_kw": round(load,3),
            "pv_kw": round(pv,3),
            "grid_base_kw": round(grid_base,3),
            "batt_kw": round(batt,3),
            "grid_opt_kw": round(grid_opt,3),
            "rate": rate,
            "soc_pct": int(round(100 * soc / cap_kwh)),
        })
    baseline_cost = round(sum(step["grid_base_kw"] * tariff_rate(step["ts"]) for step in plan), 2)
    optimized_cost = round(sum(step["grid_opt_kw"] * tariff_rate(step["ts"]) for step in plan), 2)
    savings = round(baseline_cost - optimized_cost, 2)
    return {"baseline_cost": baseline_cost, "optimized_cost": optimized_cost, "savings": savings, "plan": plan}

def optimize_battery_adaptive(
    preds: list,
    pv_factor: float = 1.0,
    batt_limit_kw: float = 2.0,
    soc_init_pct: float = 50.0,
    cap_kwh: float = 10.0,
    mode: str = "normal",
    target_savings_per_day: Optional[float] = None,
    soc_min_pct: float = 0.0,
) -> dict:
    """Adapt optimization behavior to 'mode' and optional daily savings target.
    Strategy: try progressively more aggressive discharge/charge thresholds until reaching target or best effort.
    """
    if not preds:
        return {"baseline_cost": 0.0, "optimized_cost": 0.0, "savings": 0.0, "plan": []}
    # Define threshold sets (discharge_threshold, charge_threshold)
    sets = [(1.0, 0.6), (0.9, 0.7), (0.8, 0.8)]
    if mode in ("economico", "eco", "agressivo"):
        sets = [(0.9, 0.7), (0.8, 0.8), (0.75, 0.85)]
    if mode in ("conforto", "confortavel"):
        # Pouca intervenção: não carrega da rede, só com PV; descarrega apenas em pico alto
        sets = [(1.1, -1.0)]

    best = None
    for (d_th, c_th) in sets:
        plan = []
        soc = float(np.clip(soc_init_pct, 0, 100)) / 100.0 * cap_kwh
        for p in preds:
            ts = pd.to_datetime(p["ts"]) if isinstance(p["ts"], str) else p["ts"]
            load = max(0.0, float(p["y"]))
            temp_f = _weather_forecast(ts) or estimate_temp(ts)
            pv = estimate_pv_kw(ts, temp_f, pv_factor=pv_factor)
            net = max(0.0, load - pv)
            rate = tariff_rate(ts)
            batt = 0.0
            dt = 1.0
            max_discharge_kw = soc / dt
            max_charge_kw = (cap_kwh - soc) / dt
            # Honor SOC mínimo
            soc_min_kwh = float(np.clip(soc_min_pct, 0, 100)) / 100.0 * cap_kwh
            if rate >= d_th and net > 0 and soc > soc_min_kwh:
                batt = float(min(net, batt_limit_kw, max_discharge_kw))
                # clamp to not go below SOC mínimo
                batt = min(batt, (soc - soc_min_kwh) / dt)
                soc = max(soc_min_kwh, soc - batt * dt)
            elif rate <= c_th and soc < cap_kwh and not (mode in ("conforto", "confortavel")):
                charge = float(min(batt_limit_kw, max_charge_kw))
                batt = -charge
                soc = min(cap_kwh, soc + charge * dt)
            elif net < 0 and soc < cap_kwh:
                # carregar com excedente de PV (sempre permitido)
                charge = float(min(-net, batt_limit_kw, max_charge_kw))
                batt = -charge
                soc = min(cap_kwh, soc + charge * dt)
            grid_base = net
            grid_opt = max(0.0, net - batt)
            plan.append({
                "ts": ts.isoformat(),
                "load_kw": round(load,3),
                "pv_kw": round(pv,3),
                "grid_base_kw": round(grid_base,3),
                "batt_kw": round(batt,3),
                "grid_opt_kw": round(grid_opt,3),
                "rate": rate,
                "soc_pct": int(round(100 * soc / cap_kwh)),
            })
        baseline_cost = round(sum(step["grid_base_kw"] * tariff_rate(step["ts"]) for step in plan), 2)
        optimized_cost = round(sum(step["grid_opt_kw"] * tariff_rate(step["ts"]) for step in plan), 2)
        savings = round(baseline_cost - optimized_cost, 2)
        cand = {"baseline_cost": baseline_cost, "optimized_cost": optimized_cost, "savings": savings, "plan": plan,
                "discharge_threshold": d_th, "charge_threshold": c_th}
        if best is None or cand["savings"] > best["savings"]:
            best = cand
        if target_savings_per_day is not None and savings >= target_savings_per_day:
            return cand
    return best or {"baseline_cost": 0.0, "optimized_cost": 0.0, "savings": 0.0, "plan": []}

def parse_goal(text: Optional[str]) -> Optional[dict]:
    """Parse a natural language savings goal in Portuguese, e.g., 'quero salvar 200 reais por mes'.
    Returns dict with detected amounts per month/day and derived daily target (R$)."""
    if not text:
        return None
    try:
        t = text.lower().strip()
        # extract number (allows integers/decimals)
        import re
        m = re.search(r"(\d+[\.,]?\d*)", t)
        if not m:
            return None
        amt = float(m.group(1).replace(',', '.'))
        # timeframe
        per_month = any(w in t for w in ["mês", "mes", "mensal", "mensa", "por mes", "por mês"])  # crude
        per_day = any(w in t for w in ["dia", "diário", "diaria", "por dia"])
        if per_day and not per_month:
            daily = amt
            monthly = daily * 30
        else:
            monthly = amt
            daily = monthly / 30.0
        return {"raw": text, "monthly_target": round(monthly,2), "daily_target": round(daily,2)}
    except Exception:
        return None

def tariff_rate(dt: pd.Timestamp) -> float:
    """Simple TOU tariff: peak 18-21h, mid 11-17h, resto off."""
    h = pd.to_datetime(dt).hour
    if 18 <= h <= 21:
        return 1.2
    if 11 <= h <= 17:
        return 0.8
    return 0.5

def tariff_period(dt: pd.Timestamp) -> str:
    h = pd.to_datetime(dt).hour
    if 18 <= h <= 21:
        return "peak"
    if 11 <= h <= 17:
        return "mid"
    return "off"

def compute_costs(current_ts: pd.Timestamp, current_kw: float, forecast: list, df_history: Optional[pd.DataFrame] = None) -> dict:
    """Compute current instantaneous cost and richer pricing KPIs.
    Returns: {
      rate_now, current_cost, forecast_cost_24h,
      today_cost, last24_cost,
      by_period: {off, mid, peak},
      forecast_by_period: {off, mid, peak},
      next_peak_ts: iso str or None
    }
    """
    try:
        rate_now = tariff_rate(current_ts)
        current_cost = float(current_kw) * rate_now
        # Forecast totals
        total_fc = 0.0
        fc_by = {"off": 0.0, "mid": 0.0, "peak": 0.0}
        next_peak = None
        for p in forecast:
            ts = pd.to_datetime(p["ts"]) if isinstance(p["ts"], str) else p["ts"]
            y = float(p["y"]) if p.get("y") is not None else 0.0
            rate = tariff_rate(ts)
            per = tariff_period(ts)
            c = y * rate
            total_fc += c
            fc_by[per] += c
            if next_peak is None and per == "peak":
                next_peak = ts
        today_cost = None
        last24_cost = None
        by = {"off": 0.0, "mid": 0.0, "peak": 0.0}
        if df_history is not None and len(df_history):
            dfh = df_history.copy()
            dfh["timestamp"] = pd.to_datetime(dfh["timestamp"]).dt.tz_localize(None)
            now = pd.to_datetime(current_ts).tz_localize(None)
            start_today = now.normalize()
            last24_start = now - pd.Timedelta(hours=24)
            # Today
            dft = dfh[dfh["timestamp"] >= start_today]
            if len(dft):
                today_cost = float((dft.apply(lambda r: float(r["consumption_kW"]) * tariff_rate(r["timestamp"]), axis=1)).sum())
            # Last 24h and by_period
            df24 = dfh[dfh["timestamp"] >= last24_start]
            if len(df24):
                costs_24 = df24.apply(lambda r: float(r["consumption_kW"]) * tariff_rate(r["timestamp"]), axis=1)
                last24_cost = float(costs_24.sum())
                # By period breakdown
                for _, r in df24.iterrows():
                    per = tariff_period(r["timestamp"])  # off/mid/peak
                    by[per] += float(r["consumption_kW"]) * tariff_rate(r["timestamp"])  # cost
        return {
            "rate_now": rate_now,
            "current_cost": round(current_cost, 3),
            "forecast_cost_24h": round(total_fc, 2),
            "today_cost": None if today_cost is None else round(today_cost, 2),
            "last24_cost": None if last24_cost is None else round(last24_cost, 2),
            "by_period": {k: round(v, 2) for k, v in by.items()},
            "forecast_by_period": {k: round(v, 2) for k, v in fc_by.items()},
            "next_peak_ts": next_peak.isoformat() if next_peak is not None else None,
        }
    except Exception:
        return {"rate_now": None, "current_cost": None, "forecast_cost_24h": None}

@app.route("/api/stream")
def api_stream():
    source = request.args.get("source", "live").lower()
    factor = float(request.args.get("factor", 1.0))
    pv_factor = float(request.args.get("pv_factor", 1.0))
    batt_limit = float(request.args.get("batt_limit", 2.0))
    soc_init = float(request.args.get("soc_init", 50.0))
    if source == "sim" or source == "simulacao":
        now = pd.Timestamp.now().tz_localize(None).floor("h")
        idx = pd.date_range(end=now, periods=24*14, freq="H")
        hours = idx.hour + idx.minute/60
        temp = 24 + 3*np.sin((hours-6)/24*2*np.pi)
        base = 2.5 + 0.8 * (1 + np.sin((hours-6)/24*2*np.pi)) + 0.2*np.sin((hours)/24*4*np.pi)
        noise = np.random.normal(0, 0.08, size=len(idx))
        load = np.maximum(0.2, (base + 0.05*(temp-24) + noise) * float(factor))
        df_live = pd.DataFrame({"timestamp": idx, "consumption_kW": load, "temperature_C": temp})
    else:
        try:
            df_live = load_source("db" if source == "live" else source).sort_values("timestamp").copy()
            if df_live is None or len(df_live) == 0:
                raise ValueError("empty live dataset")
        except Exception:
            # fallback to synthetic stream baseline
            now = pd.Timestamp.now().tz_localize(None).floor("h")
            idx = pd.date_range(end=now, periods=24*14, freq="H")
            hours = idx.hour + idx.minute/60
            temp = 24 + 3*np.sin((hours-6)/24*2*np.pi)
            base = 2.5 + 0.8 * (1 + np.sin((hours-6)/24*2*np.pi)) + 0.2*np.sin((hours)/24*4*np.pi)
            noise = np.random.normal(0, 0.08, size=len(idx))
            load = np.maximum(0.2, (base + 0.05*(temp-24) + noise) * float(factor))
            df_live = pd.DataFrame({"timestamp": idx, "consumption_kW": load, "temperature_C": temp})
    df_live["timestamp"] = pd.to_datetime(df_live["timestamp"]).dt.tz_localize(None)

    def gen():
        nonlocal df_live
        retry_ms = 2000
        yield f"retry: {retry_ms}\n\n"
        last = df_live.iloc[-1]
        # Battery stateful model for stream
        cap_kwh = 10.0
        soc_state_kwh = float(np.clip(soc_init, 0, 100)) / 100.0 * cap_kwh
        batt_limit_kw = float(max(0.0, batt_limit))
        from typing import Tuple
        def step_battery(soc_kwh: float, load_kw: float, pv_kw: float, dt_hours: float) -> Tuple[float, float]:
            """Return (new_soc_kwh, batt_kw), batt_kw>0 discharging to load, <0 charging"""
            net = float(load_kw) - float(pv_kw)
            batt_kw = 0.0
            if net > 0 and soc_kwh > 0:
                max_discharge_kw = soc_kwh / dt_hours
                batt_kw = float(min(net, batt_limit_kw, max_discharge_kw))
                soc_kwh = max(0.0, soc_kwh - batt_kw * dt_hours)
            elif net < 0 and soc_kwh < cap_kwh:
                surplus_kw = -net
                max_charge_kw = (cap_kwh - soc_kwh) / dt_hours
                charge_kw = float(min(surplus_kw, batt_limit_kw, max_charge_kw))
                batt_kw = -charge_kw
                soc_kwh = min(cap_kwh, soc_kwh + charge_kw * dt_hours)
            return soc_kwh, batt_kw
        while True:
            # Try external live point if configured when source == live
            point = _live_external_point() if source == "live" else None
            if point is None:
                point = _simulate_next_point(last["timestamp"], float(last["consumption_kW"]), float(last.get("temperature_C", 24.0)), factor=factor)
            # Append and compute
            df_live = pd.concat([df_live, pd.DataFrame([point])], ignore_index=True)
            df_live = df_live.tail(7*24*60).reset_index(drop=True)  # keep last ~7 days at 1-min res
            last = df_live.iloc[-1]
            # persist
            try:
                _ensure_live_table()
                _insert_live_point(point)
            except Exception:
                pass
            # Determine approx dt for battery step (based on last two points)
            if len(df_live) >= 2:
                dt_hours = float(pd.to_datetime(df_live["timestamp"]).diff().iloc[-1].total_seconds() / 3600.0)
                if not np.isfinite(dt_hours) or dt_hours <= 0:
                    dt_hours = 1.0/60.0
            else:
                dt_hours = 1.0/60.0
            # KPIs on a rolling 24h window
            if len(df_live) >= 2:
                med_dt = float(pd.Series(df_live["timestamp"]).diff().dropna().dt.total_seconds().median() / 3600.0)
                if not np.isfinite(med_dt) or med_dt <= 0:
                    med_dt = 1.0
            else:
                med_dt = 1.0
            window_steps = int(max(1, round(24.0 / med_dt)))
            window_df = df_live.tail(window_steps).copy()
            kpis = compute_kpis(window_df) if len(window_df) else {}
            # Estimate PV for last timestamp and update battery state
            ts_last = pd.to_datetime(last["timestamp"]).tz_localize(None)
            temp_last = float(last.get("temperature_C", 24.0))
            pv_now = estimate_pv_kw(ts_last, temp_last, pv_factor=pv_factor)
            load_now = float(last["consumption_kW"]) if "consumption_kW" in last else 0.0
            soc_state_kwh, batt_kw = step_battery(soc_state_kwh, load_now, pv_now, dt_hours)
            equip = {
                "pv_kw": round(pv_now, 3),
                "load_kw": round(load_now, 3),
                "battery_kw": round(batt_kw, 3),
                "grid_kw": round(max(0.0, load_now - pv_now - batt_kw), 3),
                "battery_soc": int(round(100 * soc_state_kwh / cap_kwh)),
            }
            context = generate_context(kpis, equip)
            alerts = compute_alerts(kpis, equip)
            payload = {
                "tick": {
                    "x": pd.to_datetime(last["timestamp"]).isoformat(),
                    "y": round(float(last["consumption_kW"]), 3),
                    "temp": round(float(last["temperature_C"]), 2),
                },
                "kpis": kpis,
                "equipment": equip,
                "context": context,
                "alerts": alerts,
            }
            yield f"event: tick\n" + f"data: {json.dumps(payload)}\n\n"
            time.sleep(2)

    return Response(stream_with_context(gen()), mimetype="text/event-stream", headers={
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
    })

@app.route("/")
def index():
    dev_livereload = os.environ.get("DEV_LIVERELOAD", "0") in ("1", "true", "True", "yes")
    return render_template("dashboard.html", dev_livereload=dev_livereload)

@app.route("/api/dashboard")
def api_dashboard():
    source = request.args.get("source", "db").lower()
    algo = (request.args.get("algo") or "rf").lower()
    # Normalize Portuguese synonyms
    if algo in ("floresta", "floresta_aleatoria", "floresta-aleatoria", "rf-pt"):
        algo = "rf"
    if algo in ("regressao", "regressao_linear", "regressão", "regressão_linear"):
        algo = "linear"
    if algo in ("automatico", "automático", "auto-pt"):
        algo = "auto"
    def safe_float(val, default):
        try:
            if val is None:
                return float(default)
            if isinstance(val, str) and val.strip() == "":
                return float(default)
            return float(val)
        except Exception:
            return float(default)

    factor = safe_float(request.args.get("factor"), 1.0)
    pv_factor = safe_float(request.args.get("pv_factor"), 1.0)
    batt_limit = safe_float(request.args.get("batt_limit"), 2.0)
    soc_init = safe_float(request.args.get("soc_init"), 50.0)
    mode = (request.args.get("mode") or "normal").lower()
    goal_text = request.args.get("goal")
    goal = parse_goal(goal_text)
    soc_min = safe_float(request.args.get("soc_min"), 0.0)
    # Clamp to sensible ranges
    factor = float(np.clip(factor, 0.5, 1.5))
    pv_factor = float(np.clip(pv_factor, 0.5, 2.0))
    batt_limit = float(np.clip(batt_limit, 0.0, 10.0))
    soc_init = float(np.clip(soc_init, 0.0, 100.0))
    soc_min = float(np.clip(soc_min, 0.0, 80.0))
    if source == "sim" or source == "simulacao":
        # Generate synthetic series for the last ~14 days for richer context
        now = pd.Timestamp.now().tz_localize(None)
        idx = pd.date_range(end=now, periods=24*14, freq="H")
        hours = idx.hour + idx.minute/60
        temp = 24 + 3*np.sin((hours-6)/24*2*np.pi)
        # Additional context for drift detection
        df_full = load_source(source)
        drift = compute_drift(df_full)
        base = 2.5 + 0.8 * (1 + np.sin((hours-6)/24*2*np.pi)) + 0.2*np.sin((hours)/24*4*np.pi)
        noise = np.random.normal(0, 0.08, size=len(idx))
        load = np.maximum(0.2, (base + 0.05*(temp-24) + noise) * float(factor))
        df = pd.DataFrame({"timestamp": idx, "consumption_kW": load, "temperature_C": temp})
    else:
        df = load_source(source)
    last = df.tail(7*24)
    trace = {"x": last["timestamp"].astype(str).tolist(), "y": last["consumption_kW"].round(3).tolist(), "type": "scatter", "name": "Consumo de energia (kW)", "hovertemplate": "Tempo: %{x}<br>Consumo: %{y:.2f} kW"}
    consumption = {"data":[trace], "layout":{"title":"Consumo - últimos 7 dias", "xaxis":{"title":"timestamp"}, "yaxis":{"title":"kW"}}}

    df_full = df.copy()
    df_full["timestamp"] = pd.to_datetime(df_full["timestamp"])
    df_feat = make_lag_features(df_full, n_lags=24)
    last_row = df_feat.tail(1).iloc[0]
    features = [c for c in df_feat.columns if c.startswith("lag_")] + ["hour","dayofweek","temperature_C"]
    preds = []
    current = last_row.copy()

    # Choose model per 'algo'
    active_model = None
    metrics = {**METRICS}
    # helpers to train/eval simple models with same split
    def _train_test_split(df_feat_local):
        Xl = df_feat_local[features]
        yl = df_feat_local["consumption_kW"].astype(float)
        if len(df_feat_local) >= 2:
            dt_hours_local = float(pd.Series(df_feat_local["timestamp"]).diff().dropna().dt.total_seconds().median() / 3600.0)
            if not np.isfinite(dt_hours_local) or dt_hours_local <= 0:
                dt_hours_local = 1.0
        else:
            dt_hours_local = 1.0
        steps_day_l = int(max(1, round(24.0 / dt_hours_local)))
        test_n_l = int(min(len(df_feat_local)//3, max(steps_day_l*3, 24)))
        split_l = max(1, len(df_feat_local) - test_n_l)
        return (Xl.iloc[:split_l], yl.iloc[:split_l], Xl.iloc[split_l:], yl.iloc[split_l:])

    def _mae(y_true, y_pred):
        try:
            return float(np.mean(np.abs(y_true.values - y_pred)))
        except Exception:
            return float("inf")
    if algo in ("rf", "random_forest", "randomforest"):
        active_model = MODEL
        # keep metrics from saved file
    elif algo in ("auto",):
        try:
            X_train, y_train, X_test, y_test = _train_test_split(df_feat)
            # Evaluate RF saved model
            rf_mae = _mae(y_test, MODEL.predict(X_test)) if len(X_test) else float(METRICS.get("mae_test", 0.5))
            best = ("rf", rf_mae, MODEL)
            # Linear
            try:
                lr = LinearRegression()
                lr.fit(X_train, y_train)
                mae_lr = _mae(y_test, lr.predict(X_test))
                if mae_lr < best[1]: best = ("linear", mae_lr, lr)
            except Exception:
                pass
            # Ridge
            try:
                rg = Ridge(alpha=1.0)
                rg.fit(X_train, y_train)
                mae_rg = _mae(y_test, rg.predict(X_test))
                if mae_rg < best[1]: best = ("ridge", mae_rg, rg)
            except Exception:
                pass
            # Lasso
            try:
                ls = Lasso(alpha=0.001, max_iter=10000)
                ls.fit(X_train, y_train)
                mae_ls = _mae(y_test, ls.predict(X_test))
                if mae_ls < best[1]: best = ("lasso", mae_ls, ls)
            except Exception:
                pass
            algo = best[0]
            active_model = best[2]
            metrics = {"mae_test": round(float(best[1]), 4)}
        except Exception:
            active_model = MODEL
            metrics = {**METRICS}
            algo = "rf"
    elif algo in ("linear", "lin", "lr", "linear_regression"):
        # Train a quick Linear Regression on-the-fly
        try:
            X = df_feat[features]
            y = df_feat["consumption_kW"].astype(float)
            # time-based split: last ~3 days as test
            if len(df_feat) >= 10:
                # estimate steps per day
                if len(df_feat) >= 2:
                    dt_hours = float(pd.Series(df_feat["timestamp"]).diff().dropna().dt.total_seconds().median() / 3600.0)
                    if not np.isfinite(dt_hours) or dt_hours <= 0:
                        dt_hours = 1.0
                else:
                    dt_hours = 1.0
                steps_day = int(max(1, round(24.0 / dt_hours)))
                test_n = int(min(len(df_feat)//3, max(steps_day*3, 24)))
                split = len(df_feat) - test_n
                X_train, y_train = X.iloc[:split], y.iloc[:split]
                X_test, y_test = X.iloc[split:], y.iloc[split:]
            else:
                X_train, y_train = X, y
                X_test, y_test = X.iloc[-1:], y.iloc[-1:]
            lr = LinearRegression()
            lr.fit(X_train, y_train)
            active_model = lr
            # compute MAE on test
            try:
                y_pred = lr.predict(X_test)
                mae = float(np.mean(np.abs(y_test.values - y_pred)))
                metrics = {"mae_test": round(mae, 4)}
            except Exception:
                metrics = {"mae_test": float(METRICS.get("mae_test", 0.5))}
        except Exception:
            active_model = MODEL
            metrics = {**METRICS}
            algo = "rf"
    elif algo in ("ridge",):
        try:
            X = df_feat[features]
            y = df_feat["consumption_kW"].astype(float)
            if len(df_feat) >= 2:
                dt_hours = float(pd.Series(df_feat["timestamp"]).diff().dropna().dt.total_seconds().median() / 3600.0)
                if not np.isfinite(dt_hours) or dt_hours <= 0:
                    dt_hours = 1.0
            else:
                dt_hours = 1.0
            steps_day = int(max(1, round(24.0 / dt_hours)))
            test_n = int(min(len(df_feat)//3, max(steps_day*3, 24)))
            split = max(1, len(df_feat) - test_n)
            X_train, y_train = X.iloc[:split], y.iloc[:split]
            X_test, y_test = X.iloc[split:], y.iloc[split:]
            model = Ridge(alpha=1.0)
            model.fit(X_train, y_train)
            active_model = model
            try:
                y_pred = model.predict(X_test)
                mae = float(np.mean(np.abs(y_test.values - y_pred)))
                metrics = {"mae_test": round(mae, 4)}
            except Exception:
                metrics = {"mae_test": float(METRICS.get("mae_test", 0.5))}
        except Exception:
            active_model = MODEL
            metrics = {**METRICS}
            algo = "rf"
    elif algo in ("lasso",):
        try:
            X = df_feat[features]
            y = df_feat["consumption_kW"].astype(float)
            if len(df_feat) >= 2:
                dt_hours = float(pd.Series(df_feat["timestamp"]).diff().dropna().dt.total_seconds().median() / 3600.0)
                if not np.isfinite(dt_hours) or dt_hours <= 0:
                    dt_hours = 1.0
            else:
                dt_hours = 1.0
            steps_day = int(max(1, round(24.0 / dt_hours)))
            test_n = int(min(len(df_feat)//3, max(steps_day*3, 24)))
            split = max(1, len(df_feat) - test_n)
            X_train, y_train = X.iloc[:split], y.iloc[:split]
            X_test, y_test = X.iloc[split:], y.iloc[split:]
            model = Lasso(alpha=0.001, max_iter=10000)
            model.fit(X_train, y_train)
            active_model = model
            try:
                y_pred = model.predict(X_test)
                mae = float(np.mean(np.abs(y_test.values - y_pred)))
                metrics = {"mae_test": round(mae, 4)}
            except Exception:
                metrics = {"mae_test": float(METRICS.get("mae_test", 0.5))}
        except Exception:
            active_model = MODEL
            metrics = {**METRICS}
            algo = "rf"
    else:
        # default to RF
        active_model = MODEL
        algo = "rf"
    for h in range(24):
        # update temperature feature with external forecast or diurnal estimate
        ts = pd.to_datetime(current["timestamp"]) + pd.Timedelta(hours=1)
        temp_f = _weather_forecast(ts)
        if temp_f is None:
            temp_f = estimate_temp(ts)
        current["temperature_C"] = temp_f
        x_df = pd.DataFrame([current[features]])
        yhat = float(active_model.predict(x_df)[0])
        preds.append({"ts": ts.isoformat(), "y": yhat})
        for lag in range(24,1,-1):
            current[f"lag_{lag}"] = current[f"lag_{lag-1}"]
        current["lag_1"] = yhat
        current["timestamp"] = ts
        current["hour"] = ts.hour
        current["dayofweek"] = ts.dayofweek

    # Forecast with simple uncertainty bands using MAE
    mae = float(metrics.get("mae_test", METRICS.get("mae_test", 0.5)))
    k = 1.5
    xs = [p["ts"] for p in preds]
    ys = [max(0.0, p["y"]) for p in preds]
    y_lo = [max(0.0, y - k*mae) for y in ys]
    y_hi = [max(0.0, y + k*mae) for y in ys]
    band_lower = {"x": xs, "y": y_lo, "type": "scatter", "mode": "lines", "name": "Limite inferior (p10)", "line": {"width": 0}, "showlegend": False}
    band_upper = {"x": xs, "y": y_hi, "type": "scatter", "mode": "lines", "name": "Incerteza (p10–p90)", "fill": "tonexty", "fillcolor": "rgba(96,165,250,0.18)", "line": {"width": 0}, "showlegend": True}
    median_line = {"x": xs, "y": ys, "type": "scatter", "mode": "lines+markers", "name": "Previsão (p50)", "line": {"color": "#60a5fa", "width": 2}}
    forecast = {"data":[band_lower, band_upper, median_line], "layout":{"title":"Previsão - próximas 24 horas", "xaxis":{"title":"timestamp"}, "yaxis":{"title":"kW"}}}

    # Extra datasets
    temp_trace = {"x": last["timestamp"].astype(str).tolist(), "y": last["temperature_C"].round(2).tolist(), "type": "scatter", "name": "Temperatura (°C)", "yaxis": "y2"}
    daily = df.copy()
    daily["date"] = pd.to_datetime(daily["timestamp"]).dt.date
    daily_agg = daily.groupby("date")["consumption_kW"].agg(["mean","max"]).reset_index()
    daily_series = {
        "x": daily_agg["date"].astype(str).tolist(),
        "y_mean": daily_agg["mean"].round(3).tolist(),
        "y_max": daily_agg["max"].round(3).tolist(),
    }

    kpis = compute_kpis(df)
    equipment = compute_equipment_state(df, pv_factor=pv_factor, batt_power_limit_kw=batt_limit, soc_init_pct=soc_init)
    context = generate_context(kpis, equipment)
    alerts = compute_alerts(kpis, equipment)
    anomalies = detect_anomalies(last)
    costs = compute_costs(pd.to_datetime(df.sort_values("timestamp").iloc[-1]["timestamp"]), kpis.get("current_load_kw") or 0.0, preds, df_history=df)
    target_daily = goal.get("daily_target") if goal else None
    optimization = optimize_battery_adaptive(
        preds,
        pv_factor=pv_factor,
        batt_limit_kw=batt_limit,
        soc_init_pct=soc_init,
        mode=mode,
        target_savings_per_day=target_daily,
        soc_min_pct=soc_min,
    )

    return jsonify({
        "consumption": {**consumption, "anomalies": anomalies},
        "forecast": forecast,
        "metrics": metrics,
        "temperature": {"data":[temp_trace], "layout": {"title": "Temperatura - últimos 7 dias", "xaxis": {"title": "timestamp"}, "yaxis": {"title": "°C"}}},
        "daily": daily_series,
        "kpis": kpis,
        "equipment": equipment,
        "context": context,
        "alerts": alerts,
        "source": source,
        "mode": mode,
        "goal": goal,
    "soc_min": soc_min,
        "algo": algo,
        "sim": ({"factor": factor, "pv_factor": pv_factor, "batt_limit": batt_limit, "soc_init": soc_init} if source in ("sim","simulacao") else None),
        "costs": costs,
        "optimization": optimization,
    })

@app.route("/api/export")
def api_export():
    source = request.args.get("source", "db").lower()
    rng = (request.args.get("range") or "7d").lower()
    df = load_source(source)
    df = df.sort_values("timestamp")
    end = pd.to_datetime(df["timestamp"].iloc[-1])
    if rng.endswith("d"):
        days = int(rng[:-1]) if rng[:-1].isdigit() else 7
        start = end - pd.Timedelta(days=days)
    elif rng.endswith("h"):
        hours = int(rng[:-1]) if rng[:-1].isdigit() else 24
        start = end - pd.Timedelta(hours=hours)
    else:
        start = end - pd.Timedelta(days=7)
    out = df[pd.to_datetime(df["timestamp"]) >= start]
    csv = out.to_csv(index=False)
    return Response(csv, mimetype="text/csv", headers={"Content-Disposition": f"attachment; filename=export_{rng}.csv"})

@app.route("/api/series")
def api_series():
    name = (request.args.get("name") or "consumption").lower()
    source = request.args.get("source", "db")
    df = load_source(source)
    df = df.sort_values("timestamp")
    if name == "temperature":
        return jsonify({
            "x": df["timestamp"].astype(str).tolist(),
            "y": df["temperature_C"].round(2).tolist(),
            "unit": "°C",
        })
    if name == "daily":
        daily = df.copy()
        daily["date"] = pd.to_datetime(daily["timestamp"]).dt.date
        agg = daily.groupby("date")["consumption_kW"].agg(["mean","max"]).reset_index()
        return jsonify({
            "x": agg["date"].astype(str).tolist(),
            "y_mean": agg["mean"].round(3).tolist(),
            "y_max": agg["max"].round(3).tolist(),
            "unit": "kW",
        })
    # default: consumption
    return jsonify({
        "x": df["timestamp"].astype(str).tolist(),
        "y": df["consumption_kW"].round(3).tolist(),
        "unit": "kW",
    })

def _find_free_port(candidates=(5000, 5050, 8000, 8080)):
    # Respect env var first
    if os.environ.get("PORT"):
        try:
            return int(os.environ["PORT"])
        except ValueError:
            pass
    # Try candidates
    for p in candidates:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                s.bind(("0.0.0.0", p))
            except OSError:
                continue
            return p
    # Fallback: ephemeral
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("0.0.0.0", 0))
        return s.getsockname()[1]

if __name__ == "__main__":
    port = _find_free_port()
    print(f"Starting Flask on port {port} (set PORT env var to override)")
    app.run(host="0.0.0.0", port=port, debug=True)
