package com.example.LMS.entity;

import com.example.LMS.utils.enumhelper.CollateralStatus;
import jakarta.persistence.*;

import java.math.BigDecimal;
import java.util.UUID;

@Entity
@Table(name = "collaterals")
public class Collateral {

    @Id
    @GeneratedValue
    private UUID id;

    private UUID loanId;
    private String isin;
    private BigDecimal units;
    private BigDecimal nav;
    private BigDecimal collateralValue;

    @Enumerated(EnumType.STRING)
    private CollateralStatus status;

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public UUID getLoanId() {
        return loanId;
    }

    public void setLoanId(UUID loanId) {
        this.loanId = loanId;
    }

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

    public BigDecimal getNav() {
        return nav;
    }

    public void setNav(BigDecimal nav) {
        this.nav = nav;
    }

    public BigDecimal getCollateralValue() {
        return collateralValue;
    }

    public void setCollateralValue(BigDecimal collateralValue) {
        this.collateralValue = collateralValue;
    }

    public CollateralStatus getStatus() {
        return status;
    }

    public void setStatus(CollateralStatus status) {
        this.status = status;
    }
}

