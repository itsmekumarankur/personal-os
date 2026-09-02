import { tool, createSdkMcpServer } from "@anthropic-ai/claude-agent-sdk";
import { z } from "zod";
import { searchMutualFunds } from "@/tools/searchMutualFunds";
import { getMutualFundDetails } from "@/tools/getMutualFundDetails";
import { getNavHistory } from "@/tools/getNavHistory";
import { getCategoryReturns } from "@/tools/getCategoryReturns";

const searchMutualFundsTool = tool(
  "search_mutual_funds",
  "Search for mutual funds by name or keyword using the API. Returns matching funds with fund IDs and details.",
  {
    searchQuery: z
      .string()
      .describe("The search term to find mutual funds (name or keyword)"),
  },
  async (args) => {
    return await searchMutualFunds(args);
  },
  { annotations: { readOnlyHint: true } } // Enables parallel execution
);

const getMutualFundDetailsTool = tool(
  "get_mutual_fund_details",
  "Get detailed information about a specific mutual fund including current NAV, returns, and fund details. Use the fundSlug from search results (e.g., 'parag-parikh-flexi-cap-direct-growth-100060').",
  {
    fundSlug: z
      .string()
      .describe(
        "The fund slug (e.g., 'parag-parikh-flexi-cap-direct-growth-100060'). This should be obtained from search_mutual_funds results.",
      ),
  },
  async (args) => {
    return await getMutualFundDetails(args);
  },
  { annotations: { readOnlyHint: true } } // Enables parallel execution
);

const getCategoryReturnsTool = tool(
  "get_category_returns",
  "Get category returns comparison for a mutual fund. Compare the fund's performance against its category average. Use interval parameter to control data granularity. Default navPeriod is '5Y', default interval is 30.",
  {
    fundId: z.string().describe("The fund ID (e.g., '100060')"),
    navPeriod: z
      .string()
      .default("5Y")
      .optional()
      .describe(
        "Period for NAV history: '1M', '3M', '6M', '1Y', '3Y', '5Y' (default: '5Y')",
      ),
    interval: z
      .number()
      .default(1)
      .optional()
      .describe(
        "Interval in days between data points: 1 for daily data, 30 for monthly data (default: 1)",
      ),
    investedAmount: z
      .number()
      .default(1000)
      .optional()
      .describe("Investment amount for calculation (default: 1000)"),
  },
  async (args) => {
    return await getCategoryReturns(args);
  },
  { annotations: { readOnlyHint: true } } // Enables parallel execution
);

const getNavHistoryTool = tool(
  "get_nav_history",
  "Get NAV history for a mutual fund. Returns historical NAV data with fund performance. Use interval parameter to control data granularity (1 for daily, 30 for monthly). Default navPeriod is '5Y', default interval is 1, default investedAmount is 1000.",
  {
    fundId: z.string().describe("The fund ID (e.g., '100060')"),
    navPeriod: z
      .string()
      .default("5Y")
      .optional()
      .describe(
        "Period for NAV history: '1M', '3M', '6M', '1Y', '3Y', '5Y' (default: '5Y')",
      ),
    interval: z
      .number()
      .default(1)
      .optional()
      .describe(
        "Interval in days between data points: 1 for daily data, 30 for monthly data (default: 1)",
      ),
    investedAmount: z
      .number()
      .default(1000)
      .optional()
      .describe("Investment amount for calculation (default: 1000)"),
  },
  async (args) => {
    return await getNavHistory(args);
  },
  { annotations: { readOnlyHint: true } } // Enables parallel execution
);

// Wrap the tool in an in-process MCP server
export const mutualFundsServer = createSdkMcpServer({
  name: "mutual-funds",
  version: "1.0.0",
  tools: [
    searchMutualFundsTool,
    getMutualFundDetailsTool,
    getNavHistoryTool,
    getCategoryReturnsTool,
  ],
});
