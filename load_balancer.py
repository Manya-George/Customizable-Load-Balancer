from flask import Flask, jsonify, request
import threading
import time
import requests

app = Flask(__name__)

# All known servers (including ones that may be temporarily down)
ALL_KNOWN_SERVERS = [
    "http://server1:5000",
    "http://server2:5000",
    "http://server3:5000"
]

# Active, healthy servers used by the load balancer
BACKEND_SERVERS = ALL_KNOWN_SERVERS.copy()
current_server_index = 0
HEALTH_CHECK_INTERVAL = 5  # seconds

@app.route('/')
def root():
    return 'Load Balancer is running!'

@app.route('/home', methods=['GET'])
def forward_home():
    global current_server_index

    if not BACKEND_SERVERS:
        return jsonify({"error": "No backend servers available"}), 503

    server_url = BACKEND_SERVERS[current_server_index]
    current_server_index = (current_server_index + 1) % len(BACKEND_SERVERS)

    try:
        response = requests.get(f"{server_url}/home")
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

    if not instances:
        return jsonify({"error": "No instances provided"}), 400

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

    if not instances:
        return jsonify({"error": "No instances provided"}), 400

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
    global current_server_index

    if not BACKEND_SERVERS:
        return jsonify({"error": "No backend servers available"}), 503

    server_url = BACKEND_SERVERS[current_server_index]
    current_server_index = (current_server_index + 1) % len(BACKEND_SERVERS)

    try:
        response = requests.get(f"{server_url}/{path}")
        return jsonify(response.json()), response.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": f"Failed to reach {server_url}/{path}", "details": str(e)}), 500

# Health check loop with automatic recovery
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
                pass  # server down

        if set(healthy_servers) != set(BACKEND_SERVERS):
            print("Updated healthy servers:", healthy_servers)

        BACKEND_SERVERS = healthy_servers
        time.sleep(HEALTH_CHECK_INTERVAL)

# Start health check thread
threading.Thread(target=health_check_loop, daemon=True).start()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)