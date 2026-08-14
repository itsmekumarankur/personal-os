package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.CollateralStatus;

import java.math.BigDecimal;
import java.util.UUID;

public class CollateralResponseDTO {
    private UUID collateralId;
    private String isin;
    private BigDecimal units;
    private BigDecimal nav;
    private BigDecimal collateralValue;
    private CollateralStatus status;

    public CollateralResponseDTO(
            UUID collateralId,
            String isin,
            BigDecimal units,
            BigDecimal nav,
            BigDecimal collateralValue,
            CollateralStatus status
    ) {
        this.collateralId = collateralId;
        this.isin = isin;
        this.units = units;
        this.nav = nav;
        this.collateralValue = collateralValue;
        this.status = status;
    }

    public UUID getCollateralId() { return collateralId; }
    public String getIsin() { return isin; }
    public BigDecimal getUnits() { return units; }
    public BigDecimal getNav() { return nav; }
    public BigDecimal getCollateralValue() { return collateralValue; }
    public CollateralStatus getStatus() { return status; }
}
