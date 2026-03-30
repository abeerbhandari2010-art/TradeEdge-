import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from kiteconnect import KiteConnect

app = Flask(__name__)
CORS(app)

API_KEY = os.environ.get("KITE_API_KEY")
API_SECRET = os.environ.get("KITE_API_SECRET")

kite = KiteConnect(api_key=API_KEY)

# Store access token in memory (refreshed on login)
access_token_store = {"token": None}

@app.route("/")
def index():
      return jsonify({"status": "TradeEdge backend is running"})

@app.route("/login")
def login():
      """Returns the Kite login URL for the user to authenticate."""
      login_url = kite.login_url()
      return jsonify({"login_url": login_url})

@app.route("/callback")
def callback():
      """Handles the redirect from Kite after login and generates access token."""
      request_token = request.args.get("request_token")
      if not request_token:
                return jsonify({"error": "No request_token provided"}), 400
            try:
                      data = kite.generate_session(request_token, api_secret=API_SECRET)
                      access_token_store["token"] = data["access_token"]
                      kite.set_access_token(data["access_token"])
                      return jsonify({"status": "Login successful", "access_token": data["access_token"]})
except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/set_token")
def set_token():
    """Manually set an access token (useful after first login)."""
    token = request.args.get("token")
    if not token:
              return jsonify({"error": "No token provided"}), 400
          access_token_store["token"] = token
    kite.set_access_token(token)
    return jsonify({"status": "Token set successfully"})

def ensure_token():
      """Helper to set token from store before each request."""
    if access_token_store["token"]:
              kite.set_access_token(access_token_store["token"])

@app.route("/quote")
def get_quote():
      """Get live quote for one or more instruments. Pass ?instruments=NSE:INFY,NSE:TCS"""
    ensure_token()
    instruments = request.args.get("instruments", "")
    if not instruments:
              return jsonify({"error": "No instruments provided"}), 400
          try:
                    instrument_list = [i.strip() for i in instruments.split(",")]
                    quote = kite.quote(instrument_list)
                    return jsonify(quote)
except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ltp")
def get_ltp():
      """Get Last Traded Price for instruments. Pass ?instruments=NSE:INFY,NSE:TCS"""
    ensure_token()
    instruments = request.args.get("instruments", "")
    if not instruments:
              return jsonify({"error": "No instruments provided"}), 400
          try:
                    instrument_list = [i.strip() for i in instruments.split(",")]
                    ltp = kite.ltp(instrument_list)
                    return jsonify(ltp)
except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/ohlc")
def get_ohlc():
      """Get OHLC data for instruments. Pass ?instruments=NSE:INFY,NSE:TCS"""
    ensure_token()
    instruments = request.args.get("instruments", "")
    if not instruments:
              return jsonify({"error": "No instruments provided"}), 400
          try:
                    instrument_list = [i.strip() for i in instruments.split(",")]
                    ohlc = kite.ohlc(instrument_list)
                    return jsonify(ohlc)
except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/historical")
def get_historical():
      """Get historical candle data.
          Pass ?instrument=NSE:INFY&from=2024-01-01&to=2024-01-31&interval=day"""
    ensure_token()
    instrument = request.args.get("instrument", "")
    from_date = request.args.get("from", "")
    to_date = request.args.get("to", "")
    interval = request.args.get("interval", "day")
    if not instrument or not from_date or not to_date:
              return jsonify({"error": "instrument, from, and to are required"}), 400
          try:
                    # Get instrument token first
                    quote = kite.quote([instrument])
                    instrument_token = quote[instrument]["instrument_token"]
                    data = kite.historical_data(instrument_token, from_date, to_date, interval)
                    return jsonify(data)
except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/instruments")
def get_instruments():
      """Get list of all instruments for an exchange. Pass ?exchange=NSE"""
      ensure_token()
      exchange = request.args.get("exchange", "NSE")
      try:
                instruments = kite.instruments(exchange)
                return jsonify(instruments)
except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
      port = int(os.environ.get("PORT", 5000))
      app.run(host="0.0.0.0", port=port)
