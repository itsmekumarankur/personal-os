package com.example.LMS.dto;

import jakarta.validation.Valid;
import jakarta.validation.constraints.NotEmpty;
import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

public class CreateLoanApplicationRequestDTO {
    @NotNull
    private String customerId;

    @NotNull
    private UUID loanProductId;

    @NotNull @Positive
    private BigDecimal requestedAmount;

    @NotEmpty
    private List<@Valid MutualFundRequestDTO> mutualFunds;

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

    public List<MutualFundRequestDTO> getMutualFunds() {
        return mutualFunds;
    }

    public void setMutualFunds(List<MutualFundRequestDTO> mutualFunds) {
        this.mutualFunds = mutualFunds;
    }
}
