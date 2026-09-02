package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.ApplicationStatus;

import java.math.BigDecimal;
import java.util.UUID;

public class LoanApplicationDetailsResponseDTO {
    private UUID applicationId;
    private String customerId;
    private UUID loanProductId;
    private BigDecimal requestedAmount;
    private BigDecimal eligibleAmount;
    private ApplicationStatus status;

    public LoanApplicationDetailsResponseDTO(UUID applicationId, String customerId, UUID loanProductId, BigDecimal requestedAmount, BigDecimal eligibleAmount, ApplicationStatus status) {
        this.applicationId = applicationId;
        this.customerId = customerId;
        this.loanProductId = loanProductId;
        this.requestedAmount = requestedAmount;
        this.status = status;
        this.eligibleAmount = eligibleAmount;
    }

    public UUID getApplicationId() {
        return applicationId;
    }

    public void setApplicationId(UUID applicationId) {
        this.applicationId = applicationId;
    }

    public String getCustomerId() {
        return customerId;
    }

    public void setCustomerId(String customerId) {
        this.customerId = customerId;
    }

    public UUID getLoanProductId() {
        return loanProductId;
    }

    public void setLoanProductId(UUID loanProductId) {
        this.loanProductId = loanProductId;
    }

    public BigDecimal getRequestedAmount() {
        return requestedAmount;
    }

    public void setRequestedAmount(BigDecimal requestedAmount) {
        this.requestedAmount = requestedAmount;
    }

    public ApplicationStatus getStatus() {
        return status;
    }

    public void setStatus(ApplicationStatus status) {
        this.status = status;
    }

    public BigDecimal getEligibleAmount() {
        return eligibleAmount;
    }

    public void setEligibleAmount(BigDecimal eligibleAmount) {
        this.eligibleAmount = eligibleAmount;
    }
}
