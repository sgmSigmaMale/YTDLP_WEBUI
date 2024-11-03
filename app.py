from flask import Flask, request, jsonify, render_template, send_file, Response, after_this_request
from flask_cors import CORS
from yt_dlp import YoutubeDL
from urllib.parse import urlparse, quote
import requests

app = Flask(__name__)
CORS(app)

cookieFile = './cookies.txt'

loginCreds = {
    'pornhub.com': {
        'username': "sgmbutt@gmail.com",
        'password': "chocapic88@"
    },
    'www.pornhub.com': {
        'username': "sgmbutt@gmail.com",
        'password': "chocapic88@"
    },
    'mrdeepfakes.com': {
        'username': "sbutt000",
        'password': "GwD4Ew7iJZrD@#5"
    }
}

def getMetadata(url):
    domain = urlparse(url).netloc
    loginCred = loginCreds.get(domain)
    
    ydl_opts = {
        "cookiefile": cookieFile,
        "format": 'bestvideo+bestaudio/best',
        "skip_download": True,
        'geo_bypass': True,
        'geo_bypass_country': 'CA',
        'ratelimit': 10 * 1024 * 1024,
        "retries": 3,
        "fragment_retries": 3,
        "nocheckcertificate": True,
        "http_header": {
            "User-Agent": 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.83 Safari/537.36',
        }
    }

    if loginCred:
        ydl_opts['username'] = loginCred['username']
        ydl_opts['password'] = loginCred['password']

    try:
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        return {"error": f"Error while fetching video info: {e}"}

@app.route('/')
def main():
    return render_template('index.html')

@app.route('/v', methods=['POST'])
def info():
    data = request.get_json()
    url = data.get('url')
    
    if not url:
        return jsonify({'error': "Please enter URL"}), 400
    
    info = getMetadata(url)
    if "error" in info:
        return jsonify({'error': info['error']}), 400

    return jsonify(info)

@app.route('/preview')
def preview():
    url = request.args.get('video_url')
    user_agent = request.headers.get('User-Agent', 'default-user-agent')
    video_title = request.args.get('filename', 'video')
    return stream_video(url, user_agent, video_title, request)

def stream_video(url, user_agent, video_title, request):
    domain = urlparse(url).netloc
    headers = {
        'User-Agent': user_agent,
        'Referer': f'https://{domain}',
        'Connection': 'keep-alive'
    }

    try:
        initial_response = requests.get(url, headers=headers, stream=True, allow_redirects=False, timeout=10)
        initial_response.raise_for_status()
    except requests.RequestException as e:
        return f"Error fetching video: {e}", 500

    is_streaming = 'Range' in request.headers
    chunk_size = 1024 * 512 if is_streaming else 1024 * 1024 * 10

    encoded_title = quote(f"{video_title}.mp4")
    response_headers = {
        'Content-Type': initial_response.headers.get('Content-Type', 'application/octet-stream'),
        'Content-Disposition': f'attachment; filename="{encoded_title}"'
    }
    if 'Content-Length' in initial_response.headers:
        response_headers['Content-Length'] = initial_response.headers['Content-Length']

    def generate():
        try:
            for chunk in initial_response.iter_content(chunk_size=chunk_size):
                if chunk:
                    yield chunk
        except requests.RequestException as e:
            print(f"Streaming error: {e}")

    return Response(generate(), headers=response_headers)

if __name__ == "__main__":
    app.run(port=5000, threaded=True)