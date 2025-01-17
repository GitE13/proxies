from flask import Flask, request, Response
import requests
import zlib
import io

app = Flask(__name__)

@app.route('/')
def home():
    return "Web Proxy Server"

@app.route('/proxy', methods=['GET', 'POST'])
def proxy():
    url = request.args.get('url')
    if not url:
        return "URL is required!", 400
    
    try:
        # Forward the request
        response = requests.request(
            method=request.method,
            url=url,
            headers={key: value for key, value in request.headers.items() if key != 'Host'},
            data=request.get_data(),
            cookies=request.cookies,
            allow_redirects=False
        )

        # Check for binary content type
        content_type = response.headers.get('Content-Type', '')
        if 'application/octet-stream' in content_type or 'image' in content_type:
            # Return binary data directly
            return Response(response.content, response.status_code, response.headers)

        # Handle text-based content like HTML, JSON, etc.
        if 'gzip' in response.headers.get('Content-Encoding', ''):
            buf = io.BytesIO(response.content)
            with zlib.open(buf, mode='rb') as f:
                response_content = f.read()
        elif 'deflate' in response.headers.get('Content-Encoding', ''):
            buf = io.BytesIO(response.content)
            response_content = zlib.decompress(buf.read(), -zlib.MAX_WBITS)
        else:
            response_content = response.content

        # Filter out certain headers
        excluded_headers = ['content-encoding', 'content-length', 'transfer-encoding', 'connection']
        headers = [(name, value) for name, value in response.headers.items() if name.lower() not in excluded_headers]

        # Return the response with the correct content and headers
        return Response(response_content, response.status_code, headers)

    except Exception as e:
        return f"Error: {e}", 500

if __name__ == '__main__':
    app.run(port=8080)
