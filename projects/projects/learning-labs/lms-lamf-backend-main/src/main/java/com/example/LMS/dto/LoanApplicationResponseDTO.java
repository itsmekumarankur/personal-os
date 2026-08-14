package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.ApplicationStatus;

import java.util.UUID;

public class LoanApplicationResponseDTO {
    private UUID applicationId;
    private ApplicationStatus status;
    private String reason;

    public LoanApplicationResponseDTO(UUID applicationId, ApplicationStatus status, String reason) {
        this.applicationId = applicationId;
        this.status = status;
        this.reason = reason;
    }

    public UUID getApplicationId() {
        return applicationId;
    }

    public ApplicationStatus getStatus() {
        return status;
    }

    public String getReason() {
        return reason;
    }

}
