export interface SearchItem {
    type: string;
    subType?: string;
    attributes: {
        instrumentKey?: string;
        name: string;
        shortName?: string;
        tradingSymbol?: string;
        segment: string;
        instrumentType: string;
        isin?: string;
        exchange: string;
        searchedField: string;
        exchangeToken?: string;
        expiry?: string;
        assetSymbol?: string;
        strikePrice?: number;
        assetType?: string;
        assetKey?: string;
        assetToken?: string;
    };
}
