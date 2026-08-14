import axios from "axios";
import "dotenv/config";

const API_BASE_URL = process.env.API_BASE_URL;

type GetCategoryReturnsArgs = {
  fundId: string;
  navPeriod?: string;
  investedAmount?: number;
  interval?: number;
};

export async function getCategoryReturns(args: GetCategoryReturnsArgs) {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/mutual-fund/${args.fundId}/category-returns`,
      {
        params: {
          navPeriod: args.navPeriod,
          interval: args.interval,
          investedAmount: args.investedAmount,
        },
      },
    );

    const data: any = response.data;

    // Handle API error response
    if (!data || data.success === false) {
      return {
        isError: true,
        content: [
          {
            type: "text" as const,
            text: `Failed to fetch category returns for fund ID "${args.fundId}".`,
          },
        ],
      };
    }

    // Handle empty data array
    if (!data.data || data.data.length === 0) {
      return {
        isError: true,
        content: [
          {
            type: "text" as const,
            text: `No category returns data found for fund ID "${args.fundId}".`,
          },
        ],
      };
    }

    return {
      isError: false,
      content: [
        {
          type: "text" as const,
          text: JSON.stringify(data, null, 2),
        },
      ],
    };
  } catch (error: any) {
    return {
      isError: true,
      content: [
        {
          type: "text" as const,
          text: error.message || "Failed to fetch category returns.",
        },
      ],
    };
  }
}

