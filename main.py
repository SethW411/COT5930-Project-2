import os
from flask import Flask, request, render_template, redirect, send_file
from google.cloud import storage
import datetime

app = Flask(__name__)

@app.route('/hello')
def hello_world():
    return "Hello, World!"

@app.route('/')
def index():
    image_urls = get_image_urls()

    index_html = """
    <form method="post" enctype="multipart/form-data" action="/upload">
        <div>
            <label for="file">Choose file to upload</label>
            <input type="file" id="file" name="form_file" accept="image/jpeg"/>
        </div>
        <div>
            <button>Submit</button>
        </div>
    </form>
    <h2>Uploaded Images</h2>
    <ul>
    """

    for url in image_urls:
        index_html += f'''<li><img src="{url}" alt="Uploaded Image" width="200"></li>
        <form action="/download" method="GET">
            <input type="hidden" name="file_url" value="{url}">
            <button type="submit">Download</button>
        </form>'''

    index_html += "</ul>"

    return index_html

@app.route("/download", methods=["GET"])
def download():
    file_url = request.args.get("file_url")
    signed_url = get_signed_url(file_url)
    return redirect(signed_url)

@app.route("/upload", methods=["POST"])
def upload():
    if "form_file" not in request.files:
        return "No file uploaded", 400

    file = request.files["form_file"]

    if file.filename == "":
        return "No selected file", 400

    public_url = upload_to_gcs(BUCKET_NAME, file)

    return redirect("/")

@app.route('/files')
def list_files():
    return get_image_urls()

storage_client = storage.Client()
BUCKET_NAME = 'flask-image-storage'

def upload_to_gcs(bucket_name, file):
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(file.filename)

    file.seek(0)

    blob.upload_from_file(file)

    signed_url = get_signed_url(blob.public_url)

    return signed_url

def get_image_urls():
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs()
    
    urls = [blob.public_url for blob in blobs]
    return urls

def get_signed_url(file_url, expiration_minutes=1):
    filename = file_url.split('/')[-1]
    bucket = storage_client.bucket(BUCKET_NAME)
    blob = bucket.blob(filename)

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method="GET",
    )
    return url

def generate_caption_description(image_url):
    api_key = os.getenv("GOOGLE_API_KEY") # GOOGLE_API_KEY was defined in the terminal using set GEMINI_API_KEY="my_api_key"
    api_url = "https://api.gemini.ai/generate"

    response = requests.post(api_url, json={
        "image_url": image_url,
        "api_key": api_key
    })


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)