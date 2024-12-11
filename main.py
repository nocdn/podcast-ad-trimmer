import os
import requests
import json
import time
from pydub import AudioSegment

# Step 1: Detect audio files in the current directory
audio_extensions = ['mp3', 'wav', 'ogg', 'flac', 'opus', 'm4a', 'aac']
audio_files = [f for f in os.listdir('.') if any(f.endswith(ext) for ext in audio_extensions)]

# Ensure there is at least one audio file
if not audio_files:
    print("No audio files found in the directory.")
    exit()

# Select the first audio file (you could enhance this to loop through or choose)
audio_file = audio_files[0]

# Step 2: Upload the audio file to 0x0.st
upload_url = "https://0x0.st"
with open(audio_file, 'rb') as f:
    response = requests.post(upload_url, files={'file': f})
    
if response.status_code == 200:
    audio_url = response.text.strip()
    print(f"Audio file uploaded successfully: {audio_url}")
else:
    print("Failed to upload audio file.")
    exit()

# Step 3: Push the audio to WhisperX API for transcription
whisperx_url = "https://mango.sievedata.com/v2/push"
api_key = "92hC5SLYMQU-J03Qkds2eAlu0NqzXA9ngG-FcXlhhHQ"
whisperx_payload = {
    "function": "sieve/whisperx",
    "inputs": {
        "audio": {"url": audio_url},
        "word_level_timestamps": True,
        "speaker_diarization": False,
        "speed_boost": False,
        "start_time": 0,
        "end_time": -1,
        "initial_prompt": "",
        "prefix": "",
        "language": "",
        "diarize_min_speakers": -1,
        "diarize_max_speakers": -1,
        "align_only": "",
        "batch_size": 32,
        "version": "large-v3"
    }
}

headers = {
    "Content-Type": "application/json",
    "X-API-Key": api_key
}

response = requests.post(whisperx_url, headers=headers, json=whisperx_payload)
if response.status_code == 200:
    job_id = response.json().get('id')
    print(f"WhisperX job started: {job_id}")
else:
    print("Failed to start WhisperX job.")
    exit()

# Step 4: Poll the WhisperX API to check job status and get transcription
transcription_url = f"https://mango.sievedata.com/v2/jobs/{job_id}"
transcription = None

transcription_get_headers = {
    "X-API-Key": api_key
}

# Polling loop to check if transcription is ready
while True:
    response = requests.get(transcription_url, headers=headers)
    if response.status_code == 200:
        job_data = response.json()
        if job_data.get("status") == "completed":
            transcription = job_data.get("output_0")
            break
        else:
            print("Transcription is still processing. Waiting 10 seconds before retrying...")
            time.sleep(10)
    else:
        print("Failed to retrieve transcription.")
        exit()

# Clean the transcription to remove the main text and words, keeping only larger segments
segments = [{"start": seg["start"], "end": seg["end"], "text": seg["text"].strip()} for seg in transcription.get("segments", [])]

# Now, convert this cleaned list into a format suitable for prompt
transcript = json.dumps(segments)

# Step 5: System prompt for the API to remove ads
systemPrompt = "From the provided podcast transcript, for each ad segment, extract the start time, and end time of the FULL segment (so not just the portions). Put this into a list for each segment, a start time and end time. Remember to look at the start time and end time of each part of the transcript. Take a deep breath, and this is important. Output in only JSON, with no code block or anything."

# Use OpenAI API (as you previously did) to detect ad segments using transcript
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
url = 'https://api.openai.com/v1/chat/completions'

headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_API_KEY}'
}

data = {
    "model": "gpt-4o",
    "messages": [
        {
            "role": "system",
            "content": systemPrompt
        },
        {
            "role": "user",
            "content": transcript
        }
    ]
}

response = requests.post(url, headers=headers, json=data)
jsonResponse = response.json()
justOutput = jsonResponse['choices'][0]['message']['content']

# Step 6: Parse the JSON output into a Python list of dictionaries
ad_segments = json.loads(justOutput)

# Step 7: Process the original audio file to remove ad segments
audio = AudioSegment.from_file(audio_file)
non_ad_segments = []
prev_end_time = 0

for segment in ad_segments:
    start_time = segment["start"] * 1000  # Convert to milliseconds
    end_time = segment["end"] * 1000  # Convert to milliseconds

    if prev_end_time < start_time:
        non_ad_segments.append(audio[prev_end_time:start_time])

    prev_end_time = end_time

if prev_end_time < len(audio):
    non_ad_segments.append(audio[prev_end_time:])

output_audio = sum(non_ad_segments)

# Step 8: Save the output audio with a new filename
base_name, ext = os.path.splitext(audio_file)
output_filename = f"{base_name}(trimmed-ads){ext}"
output_audio.export(output_filename, format=ext.replace('.', ''))

print(f"Processed '{audio_file}' and saved as '{output_filename}'")