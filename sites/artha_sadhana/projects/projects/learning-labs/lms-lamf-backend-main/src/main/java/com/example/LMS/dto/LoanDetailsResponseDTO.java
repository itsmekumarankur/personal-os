package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.LoanStatus;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.UUID;

public class LoanDetailsResponseDTO {
    private UUID loanId;
    private UUID applicationId;
    private UUID loanProductId;
    private BigDecimal principalAmount;
    private BigDecimal outstandingAmount;
    private LoanStatus status;
    private Instant createdAt;

    public LoanDetailsResponseDTO(
            UUID loanId,
            UUID applicationId,
            UUID loanProductId,
            BigDecimal principalAmount,
            BigDecimal outstandingAmount,
            LoanStatus status,
            Instant createdAt
    ) {
        this.loanId = loanId;
        this.applicationId = applicationId;
        this.loanProductId = loanProductId;
        this.principalAmount = principalAmount;
        this.outstandingAmount = outstandingAmount;
        this.status = status;
        this.createdAt = createdAt;
    }

    public UUID getLoanId() { return loanId; }
    public UUID getApplicationId() { return applicationId; }
    public UUID getLoanProductId() { return loanProductId; }
    public BigDecimal getPrincipalAmount() { return principalAmount; }
    public BigDecimal getOutstandingAmount() { return outstandingAmount; }
    public LoanStatus getStatus() { return status; }
    public Instant getCreatedAt() { return createdAt; }
}
