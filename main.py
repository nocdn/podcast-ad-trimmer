import os, requests

# open the file "podcast-transcript.txt" and read it into a string


with open('podcast-transcript.txt', 'r') as f:
    transcript = f.read()

systemPrompt = "From the provided podcast transcript, for each ad segment, extract the start time, and end time of the FULL segment (so not just the portions). Put this into a list for each segment, a start time and end time. Remember to look at the start time and end time of each part of the transcript. Take a deep breath, and this is important. Output in only JSON, with no code block or anything."

# read the system env variable OPENAI_API_KEY
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")

# The URL for the OpenAI API endpoint
url = 'https://api.openai.com/v1/chat/completions'

# The headers for the HTTP request
headers = {
    'Content-Type': 'application/json',
    'Authorization': f'Bearer {OPENAI_API_KEY}'
}

# The data payload for the HTTP request
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

# Send the POST request to the OpenAI API
response = requests.post(url, headers=headers, json=data)

# Print the response from the API
jsonResponse = response.json()

justOutput = jsonResponse['choices'][0]['message']['content']

print(justOutput)