package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.MfCategory;
import com.example.LMS.utils.enumhelper.ProductStatus;

import java.math.BigDecimal;
import java.util.Set;
import java.util.UUID;

public class LoanProductSummaryResponseDTO {
    private UUID id;
    private String name;
    private BigDecimal interestRate;
    private BigDecimal maxLtv;
    private ProductStatus status;
    private Set<MfCategory> mfCategories;

    public LoanProductSummaryResponseDTO(UUID id, String name, BigDecimal interestRate, BigDecimal maxLtv, ProductStatus status, Set<MfCategory> mfCategories) {
        this.id = id;
        this.name = name;
        this.interestRate = interestRate;
        this.maxLtv = maxLtv;
        this.status = status;
        this.mfCategories = mfCategories;
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

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

    public ProductStatus getStatus() {
        return status;
    }

    public void setStatus(ProductStatus status) {
        this.status = status;
    }

    public Set<MfCategory> getMfCategories() {
        return mfCategories;
    }

    public void setMfCategories(Set<MfCategory> mfCategories) {
        this.mfCategories = mfCategories;
    }
}
