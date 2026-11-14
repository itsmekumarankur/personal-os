cd /home/isha/Desktop/CODE/personal-os/projects/agentic-ai/project1-tool-agent
python -m pip install -r requirements.txt
read -rsp "Anthropic API key: " ANTHROPIC_API_KEY; echo
export ANTHROPIC_API_KEY
uvicorn main:app --reload --port 8000

Then test it:

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"What is 12 * (4 + 2)?"}'