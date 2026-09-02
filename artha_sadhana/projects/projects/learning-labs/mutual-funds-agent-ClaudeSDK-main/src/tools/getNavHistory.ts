import axios from "axios";
import "dotenv/config";

const API_BASE_URL = process.env.API_BASE_URL;

type GetNavHistoryArgs = {
  fundId: string;
  navPeriod?: string;
  interval?: number;
  investedAmount?: number;
};

export async function getNavHistory(args: GetNavHistoryArgs) {
  try {
    const response = await axios.get(
      `${API_BASE_URL}/api/mutual-fund/${args.fundId}/nav-history`,
      {
        params: {
          navPeriod: args.navPeriod,
          interval: args.interval,
          investedAmount: args.investedAmount,
        },
      },
    );

    const data = response.data;

    if (!data || !data.data) {
      return {
        isError: true,
        content: [
          {
            type: "text" as const,
            text: `No NAV history found for fund ID "${args.fundId}".`,
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
          text: error.message || "Failed to fetch NAV History.",
        },
      ],
    };
  }
}
