# Project 2: RAG Agent

Claude agent that answers questions from your own documents.
Embeddings: Voyage AI (`voyage-3.5`). Vector index: in memory. API: FastAPI. Deploy: Docker + AWS ECS Fargate behind an ALB (Terraform).

Based on Anthropic's RAG cookbook:
https://platform.claude.com/cookbook/capabilities-retrieval-augmented-generation-guide

## 1. Run locally

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_anthropic_key
export VOYAGE_API_KEY=your_voyage_key
uvicorn main:app --reload --port 8000
```

You should see `Indexed N chunks`. Then:

```
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "How many leave days carry forward to next year?"}'
```

Put your own `.md` / `.txt` files in `docs/` (replace the sample) and restart.

## 2. Docker

```
docker build -t agentic-rag:latest .
docker run -p 8000:8000 \
  -e ANTHROPIC_API_KEY=your_anthropic_key \
  -e VOYAGE_API_KEY=your_voyage_key \
  agentic-rag:latest
```

## 3. Deploy to AWS (region ap-south-1)

Replace `<account_id>` with your AWS account id.

```
aws ecr create-repository --repository-name agentic-rag --region ap-south-1

aws ecr get-login-password --region ap-south-1 | \
  docker login --username AWS --password-stdin <account_id>.dkr.ecr.ap-south-1.amazonaws.com

docker tag agentic-rag:latest <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-rag:latest
docker push <account_id>.dkr.ecr.ap-south-1.amazonaws.com/agentic-rag:latest

aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-rag/anthropic-key --secret-string 'your_anthropic_key'
aws secretsmanager create-secret --region ap-south-1 \
  --name agentic-rag/voyage-key --secret-string 'your_voyage_key'

cd infra
terraform init
terraform plan
terraform apply
```

Terraform prints `app_url`. The target needs 2 to 3 minutes to become healthy.
If it stays unhealthy, check CloudWatch log group `/ecs/agentic-rag`.

## 4. Verify

```
curl http://<app_url>/health
curl -X POST http://<app_url>/chat -H "Content-Type: application/json" \
  -d '{"message": "How many sick leave days do I get?"}'
```

## 5. Clean up

```
cd infra
terraform destroy
```

The two secrets and the ECR repository were created by CLI; delete them separately if not needed.
