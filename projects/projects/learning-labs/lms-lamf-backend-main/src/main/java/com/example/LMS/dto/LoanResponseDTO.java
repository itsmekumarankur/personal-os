package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.LoanStatus;

import java.util.UUID;

public class LoanResponseDTO {
    private UUID loanId;
    private LoanStatus status;

    public LoanResponseDTO(UUID loanId, LoanStatus status) {
        this.loanId = loanId;
        this.status = status;
    }

    public UUID getLoanId() {
        return loanId;
    }

    public LoanStatus getStatus() {
        return status;
    }
}
