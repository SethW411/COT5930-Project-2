import os
# allows interaction with the operating system. 
# it allows me to me to handle files, environmental variables (like API keys), and other system commands.


from flask import Flask, request, render_template, redirect, send_file
# Flask-        is a web framework that allows me to build web applications in Python.
# Request-      allows me to handle incoming user data, such as file uplaods.
# Render-       tempate lets me load and display html files
# Redirect-     lets me send the user to a different page

from google.cloud import storage
"""
Loads the google cloud storagge module
allows my app to upload, retrieve and list images from a storage bucket.
"""
import datetime
# allows use to temporarily provide access to download the files

# 1. Flask Hello World
app = Flask(__name__)
#   Initilizes the app

@app.route('/hello')
#   Defines a URL path that users can visit
#   the first function directly below it is the function that will run when the user accesses the route "/hello"

def hello_world():
    """Return a basic hello world response."""
    return "Hello, World!"
#   Defines a function that will read "Hello, World!"

# 2. Add other Flask endpoints
@app.route('/')
#   Defines a URL path for the home page

def index():
    """Display the upload form and list uploaded images from Cloud Storage."""

    image_urls = get_image_urls()
    #  gets all the image URLs from Cloud Storage and stores them in the image_urls variable

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
    # Upload form HTML
    # leaves an open <ul> tag to create a list of uploaded images in the next step

    for url in image_urls:
    # 7. Loop through images and add them to the HTML.
    #  url is a temporary variable that will store the value of each item in image_url
    #   as it goes through them one by one.

        index_html += f'''<li><img src="{url}" alt="Uploaded Image" width="200"></li>
        <form action="/download" method="GET">
            <input type="hidden" name="file_url" value="{url}">
            <button type="submit">Download</button>
        </form>'''
        # adds a listed item to index_html featuring the uploaded image.
        

    index_html += "</ul>"
    # closes the list after looping through the urls in image_urls.

    return index_html
    # returns the HTML content to the user

@app.route("/download", methods=["GET"])
# handles download page
def download():
    file_url =  request.args.get("file_url") # retrieves image url
    signed_url = get_signed_url(file_url) # creates a signed url
    return redirect(signed_url) # returns the signed url


@app.route("/upload", methods=["POST"])
# 8. Handle image upload

def upload():
    """Handles the image upload."""
    if "form_file" not in request.files:
        return "No file uploaded", 400
    # Checks if form_file exists in the request.files dictionary.

    file = request.files["form_file"]
    # Gets the file from request.files and assigns it to file

    if file.filename == "":
        return "No selected file", 400
    # if file is unanmed, then that means the user did not select a file before clicking submit

    public_url = upload_to_gcs(BUCKET_NAME, file)
    # Upload to Google Cloud Storage and get the public URL

    return redirect("/")
    # Redirect to the home page. Updates home page.

@app.route('/files')
def list_files():
    """Lists uploaded image files from Google Cloud Storage."""
    return get_image_urls()
# 9 & 10. List uploaded image files from Cloud Storage


storage_client = storage.Client()
BUCKET_NAME = 'flask-image-storage'
# Cloud Storage Configuration

def upload_to_gcs(bucket_name, file):
    """Upload file to Google Cloud Storage."""
    bucket = storage_client.bucket(bucket_name)
    # Connects "bucket" to the bucket_name in the function syntax (connects from me to the storage)
    blob = bucket.blob(file.filename)
    # Creates a reference file to the uploaded file selected in the function syntax

    file.seek(0)
    # Move the file stream pointer to the beginning to prevent reading the end of the file, when it is accessed again

    blob.upload_from_file(file)
    # Upload file


    signed_url = get_signed_url(blob.public_url)
    # Make the file publicly accessible


    return signed_url  # Return the public URL of the uploaded file

def get_image_urls():
    """Fetch URLs of all uploaded images from Google Cloud Storage."""
    bucket = storage_client.bucket(BUCKET_NAME)
    blobs = bucket.list_blobs()
    
    urls = [blob.public_url for blob in blobs]  # Get public URLs
    return urls

def get_signed_url(file_url, expiration_minutes=1):
    filename = file_url.split('/')[-1] # removes all the other text from the url, leaving only the filename
    bucket = storage_client.bucket(BUCKET_NAME) # connects to the bucket
    blob = bucket.blob(filename) # connects to the specified file.

    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=expiration_minutes),
        method="GET",
    )
    return url


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)
# 11. Run the Flask app