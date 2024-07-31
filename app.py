import logging
from flask import Flask, request, redirect, url_for, render_template, flash
from werkzeug.utils import secure_filename
from azure.storage.blob import BlobServiceClient
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Needed for flashing messages

# Configuration
app.config['UPLOAD_FOLDER'] = 'uploads/'
app.config['ALLOWED_EXTENSIONS'] = {'txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'}
app.config['AZURE_STORAGE_CONNECTION_STRING'] = os.getenv('AZURE_STORAGE_CONNECTION_STRING')
app.config['AZURE_CONTAINER_NAME'] = os.getenv('AZURE_CONTAINER_NAME')

# Configure logging
logging.basicConfig(level=logging.DEBUG)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            app.logger.error('No file part in the request')
            flash('No file part in the request')
            return redirect(request.url)
        file = request.files['file']
        if file.filename == '':
            app.logger.error('No selected file')
            flash('No selected file')
            return redirect(request.url)
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)

            app.logger.debug(f'File saved to {file_path}')

            app.logger.debug('Uploading to Azure Blob Storage')
            blob_service_client = BlobServiceClient.from_connection_string(app.config['AZURE_STORAGE_CONNECTION_STRING'])
            app.logger.debug('BlobServiceClient created')
            blob_client = blob_service_client.get_blob_client(container=app.config['AZURE_CONTAINER_NAME'], blob=filename)
            app.logger.debug(f'BlobClient created for container: {app.config["AZURE_CONTAINER_NAME"]}, blob: {filename}')
            with open(file_path, "rb") as data:
                blob_client.upload_blob(data)
            app.logger.debug('File uploaded to Azure Blob Storage')

            flash('File successfully uploaded')
            return redirect(url_for('index'))
    except AzureError as azure_error:
        app.logger.error(f'Azure Error occurred: {azure_error}')
        flash('An error occurred while uploading to Azure Blob Storage')
        return "Internal Server Error", 500
    except Exception as e:
        app.logger.error(f'Error occurred: {e}')
        flash('An internal error occurred')
        return "Internal Server Error", 500

if __name__ == '__main__':
    app.run(debug=True)
