import AnthropicBedrock from "@anthropic-ai/bedrock-sdk";
import { HookCallback } from "@anthropic-ai/claude-agent-sdk";

const anthropic = new AnthropicBedrock({
  awsRegion: process.env.AWS_REGION,
});

const guardrailModel = "global.anthropic.claude-haiku-4-5-20251001-v1:0"

export let lastBlockReason: string | null = null;

export const mutualFundGuardrail: HookCallback = async (input) => {
  lastBlockReason = null;
  const userPrompt = (input as any).prompt;

  if (input.hook_event_name === "UserPromptSubmit") {
    const response = await anthropic.messages.create({
      model: guardrailModel,
      max_tokens: 150,
      messages: [
        {
          role: "user",
          content: `You are a topic classifier for a mutual funds chatbot. The user is in an ongoing conversation with the assistant. Your job is to block ONLY queries that are clearly off-topic (e.g., "write me a poem", "what's the weather", "help me with my python code").

Allow the query if ANY of these apply:
- It mentions mutual funds, investments, NAV, SIP, AMC, NFO, fund performance, portfolio, asset classes, or financial markets
- It is a follow-up or clarification that likely refers to prior conversation (e.g., "tell me more", "what about returns", "compare them")
- It is a meta-question about the conversation itself (e.g., "what did I ask before", "summarize our chat", "what was my first question", "repeat that")
- It is a short greeting or conversational filler (e.g., "hi", "thanks", "ok")

Block ONLY if the query is clearly unrelated to finance AND is not a follow-up/meta question (e.g., "write code in python", "tell me a joke", "who won the cricket match").

Query: "${userPrompt}"

Respond ONLY with valid JSON:
{"ok": true} if allowed
{"ok": false, "reason": "I'm a mutual funds assistant. Your question is outside my expertise."} if blocked`,
        },
      ],
    });

    let text = response.content[0].type === "text" ? response.content[0].text : "";

    // Strip markdown code blocks if present (```json ... ```)
    const jsonMatch = text.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (jsonMatch) {
      text = jsonMatch[1].trim();
    }

    const result = JSON.parse(text);

    if (!result.ok) {
      lastBlockReason = result.reason;
      return {
        decision: "block",
        reason: result.reason,
      };
    }
  }
  return {};
};
