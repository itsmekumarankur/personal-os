package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.MfCategory;

import java.math.BigDecimal;
import java.util.Set;

public class CreateLoanProductRequestDTO {
    private String name;
    private BigDecimal interestRate;
    private BigDecimal maxLtv;
    private BigDecimal marginCallLtv;
    private BigDecimal liquidationLtv;
    private Set<MfCategory> allowedMfCategories;

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public BigDecimal getInterestRate() {
        return interestRate;
    }

    public void setInterestRate(BigDecimal interestRate) {
        this.interestRate = interestRate;
    }

    public BigDecimal getMaxLtv() {
        return maxLtv;
    }

    public void setMaxLtv(BigDecimal maxLtv) {
        this.maxLtv = maxLtv;
    }

    public BigDecimal getMarginCallLtv() {
        return marginCallLtv;
    }

    public void setMarginCallLtv(BigDecimal marginCallLtv) {
        this.marginCallLtv = marginCallLtv;
    }

    public BigDecimal getLiquidationLtv() {
        return liquidationLtv;
    }

    public void setLiquidationLtv(BigDecimal liquidationLtv) {
        this.liquidationLtv = liquidationLtv;
    }

    public Set<MfCategory> getAllowedMfCategories() {
        return allowedMfCategories;
    }

    public void setAllowedMfCategories(Set<MfCategory> allowedMfCategories) {
        this.allowedMfCategories = allowedMfCategories;
    }
}
