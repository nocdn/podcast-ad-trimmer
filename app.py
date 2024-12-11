from flask import Flask, request, jsonify
import requests
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)

# configuration
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3'}
FIREWORKS_API_KEY = os.environ.get("FIREWORKS_API_KEY")
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

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
                headers={"Authorization": f"Bearer {FIREWORKS_API_KEY}"},
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
            transcription = response.json()
            
            # summarize transcription using GPT-4o
            gpt_response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {"role": "system", "content": "Summarize the transcription you are given."},
                        {"role": "user", "content": f"{transcription}"}
                    ]
                }
            )
            
            if gpt_response.status_code == 200:
                summary = gpt_response.json()
                return jsonify({'summary': summary['choices'][0]['message']['content']})
            else:
                return jsonify({'error': f'Summary generation failed: {gpt_response.text}'}), gpt_response.status_code
            
        else:
            return jsonify({'error': f'Transcription failed: {response.text}'}), response.status_code
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5555)