#!/usr/bin/env python3
"""
app.py

Flask backend for Q&A to audio conversion, powered by OpenAI's TTS API.
Reads Q&A pairs, generates audio with pauses, returns one downloadable MP3.

Install:
  pip install flask openai python-dotenv pydub
  apt-get install ffmpeg   (or brew install ffmpeg on Mac)

Configure your API key:
  1. Copy .env.example to .env
  2. Paste your OpenAI API key into .env
  Never commit your real .env file or share it with anyone.

Run:
  python3 app.py
  Then open http://localhost:5000 in your browser
"""

from flask import Flask, render_template, request, send_file, jsonify
from pydub import AudioSegment
from openai import OpenAI
from dotenv import load_dotenv
import os
import io

# Load OPENAI_API_KEY from .env into the environment
load_dotenv()

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload

API_KEY = os.getenv('OPENAI_API_KEY')

# Models: "tts-1" = Standard (faster, cheaper, $15/1M chars)
#         "tts-1-hd" = HD (higher fidelity, $30/1M chars)
ALLOWED_MODELS = {'tts-1', 'tts-1-hd'}
ALLOWED_VOICES = {'alloy', 'ash', 'coral', 'echo', 'fable', 'onyx', 'nova', 'sage', 'shimmer'}


def get_client():
    if not API_KEY:
        raise RuntimeError(
            'No OpenAI API key found. Create a .env file (copy .env.example) '
            'and set OPENAI_API_KEY=your_key_here'
        )
    return OpenAI(api_key=API_KEY)


def parse_qa_text(text):
    """Parse plain Q&A text into a list of {'q': ..., 'a': ...} dicts."""
    lines = text.split('\n')
    pairs = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith('Q:'):
            question = line[2:].strip()
            answer = ''
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith('A:'):
                    answer = next_line[2:].strip()
                    i += 2
                else:
                    i += 1
            else:
                i += 1
            if question:
                pairs.append({'q': question, 'a': answer})
        else:
            i += 1
    return pairs


def synthesize(client, text, model, voice):
    """Call OpenAI's TTS endpoint and return an AudioSegment."""
    response = client.audio.speech.create(
        model=model,
        voice=voice,
        input=text,
        response_format='mp3',
    )
    audio_bytes = io.BytesIO(response.content)
    audio_bytes.seek(0)
    return AudioSegment.from_mp3(audio_bytes)


def generate_audio(pairs, pause_seconds, model, voice):
    """Build one combined AudioSegment: Q, pause, A, Q, pause, A, ..."""
    client = get_client()
    silence = AudioSegment.silent(duration=pause_seconds * 1000)
    combined = AudioSegment.silent(duration=300)  # small lead-in

    for idx, pair in enumerate(pairs, start=1):
        q_text = pair['q']
        a_text = pair['a']

        try:
            q_audio = synthesize(client, q_text, model, voice)
        except Exception as e:
            raise ValueError(f'Error generating audio for question {idx}: {str(e)}')

        combined += q_audio
        combined += silence

        if a_text:
            try:
                a_audio = synthesize(client, a_text, model, voice)
            except Exception as e:
                raise ValueError(f'Error generating audio for answer {idx}: {str(e)}')
            combined += a_audio

        combined += AudioSegment.silent(duration=600)  # gap before next question

    return combined


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/generate', methods=['POST'])
def generate():
    try:
        data = request.get_json()

        if not data or 'qa_text' not in data:
            return jsonify({'error': 'No Q&A text provided'}), 400

        qa_text = data.get('qa_text', '').strip()
        pause_seconds = int(data.get('pause_seconds', 10))
        model = data.get('model', 'tts-1')
        voice = data.get('voice', 'alloy')

        if model not in ALLOWED_MODELS:
            return jsonify({'error': f'Invalid model. Choose one of: {", ".join(ALLOWED_MODELS)}'}), 400
        if voice not in ALLOWED_VOICES:
            return jsonify({'error': f'Invalid voice. Choose one of: {", ".join(ALLOWED_VOICES)}'}), 400
        if not qa_text:
            return jsonify({'error': 'Q&A text cannot be empty'}), 400

        pairs = parse_qa_text(qa_text)
        if not pairs:
            return jsonify({'error': 'No valid Q&A pairs found. Use format: Q: ... / A: ...'}), 400

        audio = generate_audio(pairs, pause_seconds, model, voice)

        output = io.BytesIO()
        audio.export(output, format='mp3')
        output.seek(0)

        return send_file(
            output,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f'qa-audio-{model}-{voice}.mp3'
        )

    except RuntimeError as re_err:
        return jsonify({'error': str(re_err)}), 500
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        return jsonify({'error': f'Server error: {str(e)}'}), 500


if __name__ == '__main__':
    app.run(debug=True, host='127.0.0.1', port=5000)
