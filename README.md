# podcast-ad-trimmer

Remove ads from podcasts with Whisper and LLMs

## How it works?

It will take a transcript from Whisper by openai, which supports word-level timestamps, and then use gpt-4o to identify the ad segments. Then it uses pydub to remove the selected segments from the input audio file, and save it as a new file.

## How much does it cost?

For a 17 minute podcast, it is around 10,000 tokens, costing around $0.03 for the whole podcast (not including the cost of the Whisper API, but it is very cheap).

## How to use it?

1. Make sure you have an OpenAI API key, as an environment variable called `OPENAI_API_KEY`.
