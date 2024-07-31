from flask import Flask, request, redirect, url_for, render_template
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
import os

app = Flask(__name__)

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['AZURE_STORAGE_CONNECTION_STRING'] = 'your_connection_string_here'
app.config['AZURE_CONTAINER_NAME'] = 'your_container_name_here'

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))

        # Upload to Azure Blob Storage
        blob_service_client = BlobServiceClient.from_connection_string(app.config['AZURE_STORAGE_CONNECTION_STRING'])
        blob_client = blob_service_client.get_blob_client(container=app.config['AZURE_CONTAINER_NAME'], blob=filename)
        with open(os.path.join(app.config['UPLOAD_FOLDER'], filename), "rb") as data:
            blob_client.upload_blob(data)

        return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)
