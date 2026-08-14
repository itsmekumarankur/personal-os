import "dotenv/config";
import * as readline from "readline/promises";
import { query } from "@anthropic-ai/claude-agent-sdk";
import { mutualFundsServer } from "@/tools/server";
import { mutualFundGuardrail, lastBlockReason } from "@/guardrails/mutualFundGuardrail";

const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout,
});

let sessionId: string | undefined = undefined;

// Session-wide totals (accumulated across all turns)
const seenIds = new Set<string>();
let totalInputTokens = 0;
let totalOutputTokens = 0;
let totalCostUsd = 0;

console.log("Mutual Funds Agent — type 'exit' to quit\n");

while (true) {
  const userPrompt = await rl.question("You: ");

  if (userPrompt.trim().toLowerCase() === "exit") {
    console.log("Goodbye!");
    break;
  }

  if (!userPrompt.trim()) {
    continue;
  }

  for await (const message of query({
    prompt: userPrompt,
    options: {
      hooks: {
        UserPromptSubmit: [{ hooks: [mutualFundGuardrail] }],
      },
      mcpServers: {
        mutualFunds: mutualFundsServer,
        "exa-web-search": {
          type: "http",
          url: "https://mcp.exa.ai/mcp",
        },
      },
      allowedTools: [
        "WebFetch",
        "mcp__mutualFunds__search_mutual_funds",
        "mcp__mutualFunds__get_mutual_fund_details",
        "mcp__mutualFunds__get_nav_history",
        "mcp__mutualFunds__get_category_returns",
        "mcp__exa-web-search__*",
      ],
      permissionMode: "bypassPermissions",
      allowDangerouslySkipPermissions: true,
      env: {
        ...process.env,
        ENABLE_TOOL_SEARCH: "auto",
      },
      // Only resume on turns after the first
      ...(sessionId ? { resume: sessionId } : {}),
    },
  })) {
    if (message.type === "system" && message.subtype === "init") {
      // Capture session ID once, on the very first turn
      if (!sessionId) {
        sessionId = message.session_id;
      }

      const failedServers = message.mcp_servers.filter(
        (s) => s.status !== "connected",
      );

      if (failedServers.length > 0) {
        console.warn("Failed to connect:", failedServers);
      }
    }

    if (message.type === "assistant") {
      const msgId = message.message.id;

      // Parallel tool calls share the same ID, only count once
      if (!seenIds.has(msgId)) {
        seenIds.add(msgId);
        totalInputTokens += message.message.usage.input_tokens;
        totalOutputTokens += message.message.usage.output_tokens;
      }

      for (const block of message.message.content) {
        if (block.type === "tool_use") {
          console.log(`[tool call] ${block.name}`, block.input);
        }
      }
    } else if (message.type === "result" && message.subtype === "success") {
      if (lastBlockReason) {
        console.log(`\nA: ${lastBlockReason}\n`);
      } else {
        totalCostUsd += message.total_cost_usd;
        console.log(`\nA: ${message.result}\n`);
        console.log(
          `Session total: $${totalCostUsd.toFixed(4)} (Input: ${totalInputTokens} tokens, Output: ${totalOutputTokens} tokens)\n`,
        );
      }
    }
  }
}

rl.close();
