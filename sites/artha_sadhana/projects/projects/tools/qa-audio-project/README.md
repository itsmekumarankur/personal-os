# Q&A Audio Generator (OpenAI TTS)

Paste Q&A text, choose a voice and quality tier, and get back one downloadable
MP3 with each question, a timed pause, then the answer — repeated for every pair.

---

## 1. Install dependencies

Requires Python 3.7+ and ffmpeg.

**Install ffmpeg:**
- Mac: `brew install ffmpeg`
- Ubuntu/Debian: `sudo apt-get install ffmpeg`
- Windows: `choco install ffmpeg` (or download from ffmpeg.org and add to PATH)

**Install Python packages:**
```bash
pip install -r requirements.txt
```

---

## 2. Add your OpenAI API key

1. Copy `.env.example` to a new file named `.env`
2. Open `.env` and paste your key:
   ```
   OPENAI_API_KEY=sk-your-real-key-here
   ```
3. Save. Never share this file or commit it to a public repo — it's already
   set up to be your private local config.

Get a key at: https://platform.openai.com/api-keys
(You'll need billing enabled on your OpenAI account — TTS is pay-per-use, a
few cents will generate hours of audio.)

---

## 3. Run the app

```bash
python3 app.py
```

Open your browser to: **http://localhost:5000**

---

## 4. Using it

1. Paste your Q&A text:
   ```
   Q: What is the capital of France?
   A: The capital of France is Paris.
   ```
2. Set your recall pause (seconds between question and answer)
3. Pick **Voice quality**:
   - **Standard (tts-1)** — faster, cheaper ($15 per 1M characters)
   - **HD (tts-1-hd)** — richer, more natural ($30 per 1M characters)
4. Pick a **Voice** — Alloy, Ash, Coral, Echo, Fable, Nova, Onyx, Sage, or
   Shimmer (each has a different tone — try a couple to see what you like)
5. Click **Generate Audio File** — it downloads as one MP3 when done

---

## Cost estimate

Very roughly, 1 hour of spoken audio ≈ 48,000 characters. So:
- Standard: ~$0.72 per hour of audio
- HD: ~$1.44 per hour of audio

A typical 10-question set costs well under a cent.

---

## Troubleshooting

**"No OpenAI API key found"**
→ Make sure you created `.env` (not just `.env.example`) and it contains
your real key with no quotes: `OPENAI_API_KEY=sk-...`

**"Command 'ffmpeg' not found"**
→ Install ffmpeg using the instructions above, then restart your terminal.

**"Error generating audio... 401"**
→ Your API key is invalid or billing isn't enabled on your OpenAI account.

**"Error generating audio... 429"**
→ You've hit a rate limit. Wait a bit and try again, or generate smaller
batches at a time.

**Connection refused at localhost:5000**
→ Make sure `python3 app.py` is still running in your terminal.

---

## File structure

```
qa-audio-project/
├── app.py              # Flask backend (calls OpenAI TTS)
├── requirements.txt    # Python dependencies
├── .env.example         # Copy to .env and add your key
├── templates/
│   └── index.html      # Web interface
└── README.md
```
