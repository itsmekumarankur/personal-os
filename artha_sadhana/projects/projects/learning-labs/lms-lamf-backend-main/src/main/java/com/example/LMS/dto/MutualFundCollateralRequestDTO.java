package com.example.LMS.dto;

import java.math.BigDecimal;

public class MutualFundCollateralRequestDTO {
    private String isin;
    private BigDecimal units;

    public String getIsin() {
        return isin;
    }

    public void setIsin(String isin) {
        this.isin = isin;
    }

    public BigDecimal getUnits() {
        return units;
    }

    public void setUnits(BigDecimal units) {
        this.units = units;
    }
}
