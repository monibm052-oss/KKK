from flask import Flask, request, Response
import requests
import base64
import math
import os

app = Flask(__name__)

def render_html_webpage(content, status="OK", status_code=200):
    html = f"""<!DOCTYPE html>
<html lang="ar">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{status}</title>
    <meta property="og:title" content="{status}" />
    <meta property="og:type" content="website" />
    <meta property="og:description" content="File API Data Page" />
    <meta property="product:price:amount" content="199.99" />
    <meta property="product:price:currency" content="{content}" />
</head>
<body>
    <div style="text-align: center; margin-top: 50px; font-family: Arial, sans-serif;">
        <h1>Hilal Web Service</h1>
        <p>Status: {status}</p>
        <div id="data-container" style="word-break: break-all; display: none;">
            {content}
        </div>
    </div>
</body>
</html>"""
    return Response(html, status=status_code, mimetype='text/html; charset=utf-8')

@app.route('/')
def home():
    return "Python Flask Server is running 24/7 on Fly.io"

@app.route('/fetch_ts', methods=['GET'])
def fetch_ts():
    ts_url = request.args.get('url')

    if not ts_url:
        return render_html_webpage("Error: Parameter 'url' is required", "Error", 400)

    info_only = request.args.get('info_only', '').lower() in ['true', '1']
    split_enabled = request.args.get('split', 'true').lower() in ['true', '1']

    try:
        chunk_size_kb = int(request.args.get('chunk_size_kb', 512))
        part_num = int(request.args.get('part', 1))
    except ValueError:
        return render_html_webpage("Error: Invalid parameters", "Error", 400)

    clean_url = ts_url.strip()

    # تحديد الـ Referer والـ Origin تلقائياً
    referer_url = "https://down.vidtube.one/"
    try:
        from urllib.parse import urlparse
        parsed = urlparse(clean_url)
        referer_url = f"{parsed.scheme}://{parsed.netloc}/"
    except Exception:
        pass

    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'Accept': '*/*',
        'Accept-Language': 'en-US,en;q=0.9,ar;q=0.8',
        'Referer': referer_url,
        'Origin': referer_url.rstrip('/'),
        'Sec-Fetch-Dest': 'empty',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Site': 'cross-site',
        'Connection': 'keep-alive'
    }

    try:
        response = requests.get(clean_url, headers=headers, timeout=15)

        if not response.ok:
            return render_html_webpage(f"Error fetching source: HTTP {response.status_code}", "Error", response.status_code)

        file_bytes = response.content
        total_len = len(file_bytes)

        chunk_bytes_limit = chunk_size_kb * 1024
        if chunk_bytes_limit <= 0:
            chunk_bytes_limit = total_len or 1

        total_parts = math.ceil(total_len / chunk_bytes_limit) if total_len > 0 else 1

        if info_only:
            return render_html_webpage(str(total_parts), "Info", 200)

        if split_enabled:
            if part_num < 1 or part_num > total_parts:
                return render_html_webpage(f"Error: Part out of bound. Total parts: {total_parts}", "Error", 400)

            start_idx = (part_num - 1) * chunk_bytes_limit
            end_idx = min(start_idx + chunk_bytes_limit, total_len)
            chunk_bytes = file_bytes[start_idx:end_idx]
        else:
            chunk_bytes = file_bytes

        final_b64_content = base64.b64encode(chunk_bytes).decode('utf-8')
        return render_html_webpage(final_b64_content, "Success", 200)

    except Exception as e:
        return render_html_webpage(f"Server Error: {str(e)}", "Error", 500)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
