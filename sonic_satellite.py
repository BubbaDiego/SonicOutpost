from flask import Flask, request, jsonify, render_template, send_file
import requests
import os
import json
import logging
from datetime import datetime

app = Flask(__name__)

# Configuration
#LOCAL_SERVER_URL = "http://localhost:5001"  # Update with ngrok or other URL if necessary
LOCAL_SERVER_URL = "http://192.168.50.123:5001"

PORTFOLIO_FILE = "portfolio.json"

logging.basicConfig(
    filename='satellite.log',  # Name of the log file
    level=logging.DEBUG,       # Log level: DEBUG, INFO, WARNING, ERROR, CRITICAL
    format='%(asctime)s - %(levelname)s - %(message)s'
)


@app.route('/')
def home():
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"Sonic Satellite: ONLINE - {current_time}"

@app.route('/get-console-logs', methods=['GET'])
def get_console_logs():
    """
    Serve the latest console logs.
    """
    try:
        with open('satellite.log', 'r') as log_file:
            logs = log_file.readlines()[-100:]  # Read the last 100 lines
        return jsonify({"logs": logs}), 200
    except FileNotFoundError:
        return jsonify({"logs": ["No logs found. Start interacting with the app to generate logs."]}), 200

@app.route('/ping-web-station', methods=['GET'])
def ping_web_station():
    try:
        response = requests.get(f"{LOCAL_SERVER_URL}/", timeout=15)
        if response.status_code == 200 and "Sonic Web Station is running!" in response.text:
            logging.info("Web Station is online.")
            return jsonify({"status": "online"}), 200
        else:
            logging.warning("Web Station responded, but status is not 200.")
            return jsonify({"status": "offline"}), 200
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception: {e}")
        return jsonify({"status": "offline", "error": str(e)}), 200

@app.route('/monsters', methods=['GET', 'POST'])
def monsters():
    """
    Display a string of Unicode monster faces with spaces in between.
    """
    monster_faces = ["👹", "👺", "👻 👻👻", "🧛‍♂️", "🧟‍♂️"]
    if request.method == 'POST':
        return jsonify({"message": "Monsters POST received!", "monsters": monster_faces}), 200
    return f"MONSTERS: {' '.join(monster_faces)}"

@app.route('/view-portfolio', methods=['GET'])
def view_portfolio():
    try:
        with open(PORTFOLIO_FILE, 'r') as f:
            portfolio_data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        portfolio_data = {"positions": []}

    return render_template('portfolio_editor.html', portfolio=portfolio_data)

@app.route('/upload-portfolio', methods=['POST'])
def upload_portfolio():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files['file']

    if file.filename == '' or not file.filename.endswith('.json'):
        return jsonify({"error": "Invalid file type. Please upload a JSON file."}), 400

    try:
        portfolio_data = json.load(file)
        with open(PORTFOLIO_FILE, 'w') as f:
            json.dump(portfolio_data, f, indent=4)
        return jsonify({"message": "Portfolio updated successfully."}), 200
    except json.JSONDecodeError:
        return jsonify({"error": "Invalid JSON format."}), 400

@app.route('/backup-portfolio', methods=['GET'])
def backup_portfolio():
    if not os.path.exists(PORTFOLIO_FILE):
        return jsonify({"error": "Portfolio file not found."}), 404

    return send_file(PORTFOLIO_FILE, as_attachment=True)

@app.route('/sync-portfolio', methods=['POST'])
def sync_portfolio():
    try:
        with open(PORTFOLIO_FILE, 'r') as f:
            portfolio_data = json.load(f)
        logging.debug(f"Sending portfolio data: {portfolio_data}")

        response = requests.post(f"{LOCAL_SERVER_URL}/process-portfolio", json=portfolio_data)
        logging.debug(f"Response: {response.text}")

        return jsonify({"message": "Portfolio synced successfully.", "response": response.json()}), response.status_code
    except (FileNotFoundError, json.JSONDecodeError):
        return jsonify({"error": "Portfolio file not found or invalid."}), 500
    except requests.exceptions.RequestException as e:
        logging.error(f"Request exception: {e}")
        return jsonify({"error": str(e)}), 500

@app.route('/test-remote', methods=['POST'])
def test_remote():
    try:
        portfolio_data = {
            "positions": [
                {
                    "asset": "BTC",
                    "position_type": "long",
                    "leverage": "2x",
                    "value": 50000,
                    "size": 1.0,
                    "collateral": 25000,
                    "entry_price": 45000,
                    "mark_price": 50000,
                    "liquidation_price": 40000
                }
            ],
            "imported_timestamp": "2023-01-01T12:00:00Z"
        }

        response = requests.post(f"{LOCAL_SERVER_URL}/process-portfolio", json=portfolio_data)
        return (response.content, response.status_code, response.headers.items())
    except requests.exceptions.RequestException as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
