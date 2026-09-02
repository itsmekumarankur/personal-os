<div align="center">

# Mutual Funds Agent

<p>
  <strong>An AI-powered mutual fund research agent built with Claude Agent SDK</strong>
</p>

<p>
  <img src="https://img.shields.io/badge/Claude-Agent%20SDK-blueviolet?style=for-the-badge&logo=anthropic&logoColor=white" alt="Claude Agent SDK" />
  <img src="https://img.shields.io/badge/TypeScript-3178C6?style=for-the-badge&logo=typescript&logoColor=white" alt="TypeScript" />
  <img src="https://img.shields.io/badge/Node.js-339933?style=for-the-badge&logo=nodedotjs&logoColor=white" alt="Node.js" />
  <img src="https://img.shields.io/badge/Amazon-Bedrock-FF9900?style=for-the-badge&logo=amazonaws&logoColor=white" alt="Amazon Bedrock" />
</p>

<p>
  <img src="https://img.shields.io/badge/MCP-Model%20Context%20Protocol-orange?style=flat-square" alt="MCP" />
  <img src="https://img.shields.io/badge/License-MIT-green?style=flat-square" alt="License" />
</p>

</div>

---

> **Self-host the Backend API for best performance!**
>
> The default API (`upstocks-api.onrender.com`) runs on Render's free tier and spins down after inactivity, causing slow cold starts. For reliable usage, self-host the API: **[Upstocks-API](https://github.com/uditya-kumar/Upstocks-API)**

---

## Overview

A conversational AI agent that analyzes Indian mutual funds using natural language. Ask questions like *"Analyse Parag Parikh Flexi Cap fund"* and get detailed insights including NAV history, category comparisons, and performance metrics.

## Tech Stack

| Technology | Purpose |
|------------|---------|
| Claude Agent SDK | AI agent framework with tool orchestration |
| TypeScript | Type-safe development |
| Node.js | Runtime environment |
| Amazon Bedrock | Claude model provider |
| Axios | HTTP client for API calls |
| Zod | Schema validation for MCP tools |

## Features

| Feature | Description |
|---------|-------------|
| **Fund Search** | Search mutual funds by name or keyword |
| **Fund Details** | Get comprehensive fund information including NAV, AUM, expense ratio |
| **NAV History** | Retrieve historical NAV data with configurable periods (1M to 5Y) |
| **Category Comparison** | Compare fund performance against category averages |
| **Web Search** | Integrated Exa web search for additional research |

## MCP Tools

The agent exposes the following tools via Model Context Protocol:

```
mcp__mutualFunds__search_mutual_funds      - Search for mutual funds
mcp__mutualFunds__get_mutual_fund_details  - Get detailed fund information
mcp__mutualFunds__get_nav_history          - Retrieve NAV history
mcp__mutualFunds__get_category_returns     - Get category performance comparison
```

## Project Structure

```
mutual-funds-agent/
├── src/
│   ├── agent.ts              # Main agent entry point
│   ├── tools/
│   │   ├── server.ts         # MCP server configuration
│   │   ├── searchMutualFunds.ts
│   │   ├── getMutualFundDetails.ts
│   │   ├── getNavHistory.ts
│   │   └── getCategoryReturns.ts
│   └── types/
│       └── index.ts          # TypeScript interfaces
├── .env                      # Environment variables
├── package.json
└── tsconfig.json
```

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/mutual-funds-agent.git
cd mutual-funds-agent

# Install dependencies
npm install
```

## Configuration

Copy `.env.example` to `.env` and configure your authentication:

```bash
cp .env.example .env
```

### Authentication Options

Choose **one** of the following authentication methods:

<details>
<summary><strong>Option 1: Anthropic API (Recommended)</strong></summary>

The simplest option for personal use. Get an API key from [Anthropic Console](https://console.anthropic.com/).

```env
ANTHROPIC_API_KEY=your_anthropic_api_key
API_BASE_URL=https://upstocks-api.onrender.com
```

</details>

<details>
<summary><strong>Option 2: Amazon Bedrock</strong></summary>

For AWS users with Bedrock access.

```env
CLAUDE_CODE_USE_BEDROCK=1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
AWS_REGION=us-east-1
API_BASE_URL=https://upstocks-api.onrender.com
```

**Setup steps:**
1. Enable Anthropic models in [Amazon Bedrock Console](https://console.aws.amazon.com/bedrock)
2. Configure IAM permissions for `bedrock:InvokeModel` and `bedrock:InvokeModelWithResponseStream`

</details>

<details>
<summary><strong>Option 3: Google Vertex AI</strong></summary>

For Google Cloud users.

```env
CLAUDE_CODE_USE_VERTEX=1
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account.json
ANTHROPIC_VERTEX_PROJECT_ID=your_project_id
CLOUD_ML_REGION=us-east5
API_BASE_URL=https://upstocks-api.onrender.com
```

</details>

## Usage

```bash
npm start
```

### Example Prompts

```
"Analyse the fund Parag Parikh Flexi Cap Direct Growth"
"Compare HDFC Balanced Advantage Fund with its category"
"Show me NAV history for SBI Bluechip Fund for last 3 years"
"Search for best large cap mutual funds"
```

### Sample Output

```
[tool call] search_mutual_funds { searchQuery: 'parag parikh flexi cap' }
[tool call] get_mutual_fund_details { fundSlug: 'parag-parikh-flexi-cap-direct-growth-100060' }

Q: Analyse the fund parag parikh flexi cap direct growth
A: Here's the analysis of Parag Parikh Flexi Cap Direct Growth...

Total cost: $0.0234 (Input: 1250 tokens, Output: 890 tokens)
```

## Environment Variables

### Authentication (Choose one)

| Variable | Provider | Description |
|----------|----------|-------------|
| `ANTHROPIC_API_KEY` | Anthropic API | API key from [console.anthropic.com](https://console.anthropic.com/) |
| `CLAUDE_CODE_USE_BEDROCK` | AWS Bedrock | Set to `1` to enable Bedrock |
| `AWS_ACCESS_KEY_ID` | AWS Bedrock | AWS access key |
| `AWS_SECRET_ACCESS_KEY` | AWS Bedrock | AWS secret key |
| `AWS_REGION` | AWS Bedrock | AWS region (e.g., `us-east-1`) |
| `CLAUDE_CODE_USE_VERTEX` | Google Vertex | Set to `1` to enable Vertex AI |
| `ANTHROPIC_VERTEX_PROJECT_ID` | Google Vertex | GCP project ID |
| `CLOUD_ML_REGION` | Google Vertex | GCP region (e.g., `us-east5`) |

### Other Configuration

| Variable | Required | Description |
|----------|----------|-------------|
| `ANTHROPIC_MODEL` | No | Model override (e.g., `claude-sonnet-4-5-20250514`) |
| `API_BASE_URL` | Yes | Mutual funds API endpoint |

## API Reference

The agent connects to a mutual funds API with the following endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/mutual-fund/search` | GET | Search mutual funds |
| `/api/mutual-fund` | GET | Get fund details |
| `/api/mutual-fund/:id/nav-history` | GET | Get NAV history |
| `/api/mutual-fund/:id/category-returns` | GET | Get category returns |

> **Backend API**: The backend API for this project is available at [Upstocks-API](https://github.com/uditya-kumar/Upstocks-API.git)

## License

MIT