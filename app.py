from flask import Flask, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3'}
API_KEY = 'cQlEpRGJbif9YQMGwGH8HWmUG1kkbBalQAumk6KMjLm9tFTF'

# create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/transcribe', methods=['POST'])
def transcribe_audio():
    # check if file is present in request
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400
    
    file = request.files['file']
    
    # check if file is empty
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400
    
    # check if file is allowed
    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed'}), 400
    
    try:
        # save file temporarily
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # transcribe file
        with open(filepath, "rb") as f:
            response = requests.post(
                "https://audio-prod.us-virginia-1.direct.fireworks.ai/v1/audio/transcriptions",
                headers={"Authorization": f"Bearer {API_KEY}"},
                files={"file": f},
                data={
                    "vad_model": "silero",
                    "alignment_model": "tdnn_ffn",
                    "preprocessing": "none",
                    "language": "en",
                    "temperature": "0.2",
                    "timestamp_granularities": "word",
                    "response_format": "verbose_json"
                },
            )
        
        # clean up temporary file
        os.remove(filepath)
        
        if response.status_code == 200:
            return jsonify(response.json())
        else:
            return jsonify({'error': f'Transcription failed: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)