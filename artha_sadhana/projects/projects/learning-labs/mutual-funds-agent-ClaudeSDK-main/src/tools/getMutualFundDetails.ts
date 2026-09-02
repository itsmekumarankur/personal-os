import axios from "axios";
import 'dotenv/config'

const API_BASE_URL = process.env.API_BASE_URL;

type getMutualFundDetailsArgs = {
    fundSlug: string
}

export async function getMutualFundDetails(args: getMutualFundDetailsArgs) {
    
    try {
        const cleanSlug = args.fundSlug.trim().toLowerCase().replace(/\s+/g, '-');
    
        const response = await axios.get(`${API_BASE_URL}/api/mutual-fund`, {
            params: {fund: cleanSlug}
        })

        const data: any = response.data;

        // Handle empty data - check if fundBasics exists (key field in response)
        if (!data || !data.fundBasics) {
            return {
                isError: true,
                content: [{
                    type: "text" as const,
                    text: `No data found for fund "${args.fundSlug}". Please verify the fund slug is correct. Try searching for the fund first using search_mutual_funds.`
                }]
            };
        }
        
        return {
            isError: false,
            content: [{
                type: "text" as const,
                text: JSON.stringify(data, null, 2)
            }]
        };

    } catch (error: any) {
        return {
            isError: true,
            content: [{
                type: "text" as const,
                text: error.message || "Failed to fetch mutual fund details."
            }]
        };
    }

}