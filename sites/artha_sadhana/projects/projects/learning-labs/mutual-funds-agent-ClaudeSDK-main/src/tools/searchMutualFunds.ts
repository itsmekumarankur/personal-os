import axios from "axios";
import { SearchItem } from "@/types";
import 'dotenv/config'

const API_BASE_URL = process.env.API_BASE_URL;

type searchMutualFundsArgs = {
    searchQuery: string
}

export async function searchMutualFunds(args: searchMutualFundsArgs) {
    try {
        const response = await axios.get(`${API_BASE_URL}/api/mutual-fund/search`, {
            params: {query: args.searchQuery}
        })

        const data: any = response.data;

        const searchList: SearchItem[] = data?.data?.searchList || [];
        
        if (searchList.length === 0){
            return {
                isError: true,
                content: [{type: "text" as const, text: `No mutual funds found matching "${args.searchQuery}". Please try a different keyword.`}]
            }
        }

        // Filtering only mutual fund from the searchList result
        const mutualFunds = searchList.filter(item => item.attributes.segment === "MF")
        
        if (mutualFunds.length === 0){
            return {
                isError: true,
                content: [{type: "text" as const, text: `No mutual funds found matching "${args.searchQuery}". Please try a different keyword.`}]
            }
        }

        return {
            isError: false,
            content: [{
                type: "text" as const,
                text: JSON.stringify(mutualFunds, null, 2)
            }]
        }

    } catch (error: any) {
        return {
            isError: true,
            content: [{
                type: "text" as const,
                text: error.message || "Failed to search mutual funds."
            }]
        }
    }
}