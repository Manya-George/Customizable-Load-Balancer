from flask import Flask, jsonify, request
from consistent_hash import ConsistentHashMap
import threading
import time
import requests
import random

app = Flask(__name__)

# Load balancer settings
ALL_KNOWN_SERVERS = [
    "http://server1:5000",
    "http://server2:5000",
    "http://server3:5000"
]
BACKEND_SERVERS = ALL_KNOWN_SERVERS.copy()
HEALTH_CHECK_INTERVAL = 5  # seconds

# Initialize consistent hash map
hash_map = ConsistentHashMap(num_slots=512, num_virtuals=9)

# Helper: extract numeric ID from server URL
def extract_server_id(url):
    try:
        return int(url.replace("http://server", "").replace(":5000", ""))
    except:
        return None

# Flask routes

@app.route('/')
def root():
    return 'Load Balancer is running!'

@app.route('/home', methods=['GET'])
def forward_home():
    if not BACKEND_SERVERS:
        return jsonify({"error": "No backend servers available"}), 503

    # Use consistent hashing to pick server
    request_id = random.randint(1, 100000)
    server_id = hash_map.get_server(request_id)
    server_url = f"http://server{server_id}:5000"

    try:
        response = requests.get(f"{server_url}/home", timeout=2)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to reach {server_url}", "details": str(e)}), 500

@app.route('/heartbeat', methods=['GET'])
def heartbeat():
    return "", 200

@app.route('/rep', methods=['GET'])
def replicas():
    replicas = [url.replace("http://", "").replace(":5000", "") for url in BACKEND_SERVERS]
    return jsonify({
        "count": len(BACKEND_SERVERS),
        "replicas": replicas
    }), 200

@app.route('/add', methods=['POST'])
def add_replicas():
    data = request.get_json()
    instances = data.get("instances", [])
    added = []

    for name in instances:
        url = f"http://{name}:5000"
        if url not in ALL_KNOWN_SERVERS:
            ALL_KNOWN_SERVERS.append(url)
            added.append(name)

    return jsonify({
        "message": "Replicas added",
        "added": added,
        "total_known": len(ALL_KNOWN_SERVERS)
    }), 200

@app.route('/rm', methods=['DELETE'])
def remove_replicas():
    data = request.get_json()
    instances = data.get("instances", [])
    removed = []

    for name in instances:
        url = f"http://{name}:5000"
        if url in ALL_KNOWN_SERVERS:
            ALL_KNOWN_SERVERS.remove(url)
            removed.append(name)

    return jsonify({
        "message": "Replicas removed",
        "removed": removed,
        "remaining_known": len(ALL_KNOWN_SERVERS)
    }), 200

@app.route('/<path:path>', methods=['GET'])
def fallback_proxy(path):
    if not BACKEND_SERVERS:
        return jsonify({"error": "No backend servers available"}), 503

    request_id = random.randint(1, 100000)
    server_id = hash_map.get_server(request_id)
    server_url = f"http://server{server_id}:5000"

    try:
        response = requests.get(f"{server_url}/{path}", timeout=2)
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to reach {server_url}/{path}", "details": str(e)}), 500

# Background thread to check server health and update hash ring
def health_check_loop():
    global BACKEND_SERVERS
    while True:
        healthy_servers = []
        for url in ALL_KNOWN_SERVERS:
            try:
                resp = requests.get(f"{url}/heartbeat", timeout=2)
                if resp.status_code == 200:
                    healthy_servers.append(url)
            except requests.exceptions.RequestException:
                continue

        # Only update if there are changes
        if set(healthy_servers) != set(BACKEND_SERVERS):
            print("[INFO] Updated healthy servers:", healthy_servers)

            # Remove old servers from hash ring
            for url in BACKEND_SERVERS:
                sid = extract_server_id(url)
                if sid:
                    hash_map.remove_server(sid)

            # Add new servers to hash ring
            for url in healthy_servers:
                sid = extract_server_id(url)
                if sid:
                    hash_map.add_server(sid)

            BACKEND_SERVERS = healthy_servers

        time.sleep(HEALTH_CHECK_INTERVAL)

# Start background health check
threading.Thread(target=health_check_loop, daemon=True).start()

# Start Flask app
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
