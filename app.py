from flask import Flask, request, jsonify, redirect, render_template_string
import psycopg2
import os
import random
import string
import time

app = Flask(__name__)

def get_db():
    for i in range(10):
        try:
            conn = psycopg2.connect(
                host=os.environ.get("DB_HOST", "db"),
                database=os.environ.get("DB_NAME", "urlshortener"),
                user=os.environ.get("DB_USER", "aurora"),
                password=os.environ.get("DB_PASSWORD", "password")
            )
            return conn
        except psycopg2.OperationalError:
            print(f"DB not ready, retrying... ({i+1}/10)")
            time.sleep(2)
    raise Exception("Could not connect to database")

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS urls (
            id SERIAL PRIMARY KEY,
            short_code VARCHAR(10) UNIQUE NOT NULL,
            original_url TEXT NOT NULL,
            clicks INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT NOW()
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

def generate_code():
    return ''.join(random.choices(string.ascii_letters + string.digits, k=6))

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>URL Shortener</title>
    <style>
        body { font-family: monospace; background: #0f0f0f;
               color: #00ff00; padding: 40px; }
        h1 { color: #00ff00; }
        .card { background: #1a1a1a; border: 1px solid #00ff00;
                padding: 20px; margin: 10px 0; border-radius: 4px; }
        input { background: #1a1a1a; color: #00ff00; border: 1px solid #00ff00;
                padding: 8px; width: 60%; margin: 10px 0; }
        button { background: #00ff00; color: #000; border: none;
                 padding: 8px 16px; cursor: pointer; font-weight: bold; }
        table { width: 100%; border-collapse: collapse; margin-top: 10px; }
        th, td { border: 1px solid #00ff00; padding: 8px; text-align: left; }
        a { color: #00ff00; }
        .result { margin-top: 10px; padding: 10px; background: #0a2a0a; }
    </style>
</head>
<body>
    <h1>URL Shortener</h1>

    <div class="card">
        <h2>Shorten a URL</h2>
        <input type="text" id="url" placeholder="https://example.com/very/long/url">
        <br>
        <button onclick="shorten()">Shorten</button>
        <div class="result" id="result" style="display:none"></div>
    </div>

    <div class="card">
        <h2>Recent URLs</h2>
        <table id="urls-table">
            <tr><th>Short Code</th><th>Original URL</th><th>Clicks</th><th>Created</th></tr>
        </table>
        <button onclick="loadUrls()" style="margin-top:10px">Refresh</button>
    </div>

    <script>
        async function shorten() {
            const url = document.getElementById('url').value;
            const res = await fetch('/api/shorten', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({url: url})
            });
            const data = await res.json();
            const result = document.getElementById('result');
            result.style.display = 'block';
            if (data.short_url) {
                result.innerHTML = 'Short URL: <a href="' + data.short_url + '" target="_blank">' + data.short_url + '</a>';
                loadUrls();
            } else {
                result.innerHTML = 'Error: ' + data.error;
            }
        }

        async function loadUrls() {
            const res = await fetch('/api/urls');
            const data = await res.json();
            const table = document.getElementById('urls-table');
            table.innerHTML = '<tr><th>Short Code</th><th>Original URL</th><th>Clicks</th><th>Created</th></tr>';
            data.urls.forEach(u => {
                table.innerHTML += '<tr><td><a href="/s/' + u.short_code + '" target="_blank">' + u.short_code + '</a></td><td>' + u.original_url.substring(0, 50) + '...</td><td>' + u.clicks + '</td><td>' + u.created_at + '</td></tr>';
            });
        }

        loadUrls();
    </script>
</body>
</html>
"""

@app.route("/")
def home():
    return render_template_string(HTML)

@app.route("/api/shorten", methods=["POST"])
def shorten():
    data = request.get_json()
    if not data or "url" not in data:
        return jsonify({"error": "no url provided"}), 400

    original_url = data["url"]
    if not original_url.startswith("http"):
        return jsonify({"error": "invalid url"}), 400

    short_code = generate_code()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO urls (short_code, original_url)
            VALUES (%s, %s)
        """, (short_code, original_url))
        conn.commit()
        cur.close()
        conn.close()
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    base_url = os.environ.get("BASE_URL", "http://13.201.5.197")
    return jsonify({
        "short_url": f"{base_url}/s/{short_code}",
        "short_code": short_code
    })

@app.route("/api/urls")
def list_urls():
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("""
            SELECT short_code, original_url, clicks, created_at
            FROM urls
            ORDER BY created_at DESC
            LIMIT 20
        """)
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({
            "urls": [
                {
                    "short_code": r[0],
                    "original_url": r[1],
                    "clicks": r[2],
                    "created_at": str(r[3])
                } for r in rows
            ]
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5001)
EOF
