import os
import requests
from flask import Flask, jsonify, request
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

TWELVEDATA_API_KEY = os.environ.get("TWELVEDATA_API_KEY", "")
TD_BASE = "https://api.twelvedata.com"

# ── Twelve Data symbol map for NSE indices ──
INDEX_SYMBOLS = {
    "NIFTY 50:NSE":         "NIFTY",
    "NIFTY BANK:NSE":       "BANKNIFTY",
    "BSE SENSEX:BSE":       "SENSEX",
    "INDIA VIX:NSE":        "INDIAVIX",
    "NIFTY MIDCAP 50:NSE":  "MIDCPNIFTY",
    "NIFTY FIN SERVICE:NSE":"FINNIFTY",
    "NIFTY NEXT 50:NSE":    "NIFTYNXT50",
}


@app.route("/")
def index():
    return jsonify({"status": "TradeEdge backend is running"})


@app.route("/api/quotes")
def quotes():
    """
    Proxy endpoint for Twelve Data price quotes.
    Called by the frontend as: /api/quotes?symbols=NIFTY+50:NSE,NIFTY+BANK:NSE,...
    Returns: { ok: true, quotes: { "SYMBOL": { price, change_percent } } }
    """
    symbols_param = request.args.get("symbols", "")
    if not symbols_param:
        return jsonify({"ok": False, "error": "No symbols provided"}), 400

    if not TWELVEDATA_API_KEY:
        return jsonify({"configured": False, "ok": False, "error": "API key not configured"}), 500

    symbols = [s.strip() for s in symbols_param.split(",") if s.strip()]
    if not symbols:
        return jsonify({"ok": False, "error": "No valid symbols"}), 400

    try:
        resp = requests.get(
            f"{TD_BASE}/quote",
            params={
                "symbol": ",".join(symbols),
                "apikey": TWELVEDATA_API_KEY,
                "dp": 2,
            },
            timeout=10
        )
        if not resp.ok:
            return jsonify({"ok": False, "error": f"Upstream error {resp.status_code}"}), 502

        data = resp.json()

        # Normalise: single symbol returns dict, multiple returns dict of dicts
        if isinstance(data, dict) and "symbol" in data:
            data = {data["symbol"]: data}

        quotes_out = {}
        for sym, info in data.items():
            if isinstance(info, dict) and "close" in info:
                price = float(info.get("close") or info.get("previous_close") or 0)
                chg   = float(info.get("percent_change") or 0)
                quotes_out[sym] = {"price": price, "change_percent": chg}

        return jsonify({"ok": True, "quotes": quotes_out})

    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/api/status")
def status():
    configured = bool(TWELVEDATA_API_KEY)
    return jsonify({"configured": configured, "ok": True})


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
