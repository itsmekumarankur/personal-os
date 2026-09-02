package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.ProductStatus;

import java.time.Instant;
import java.util.UUID;

public class LoanProductResponseDTO {
    private UUID id;
    private ProductStatus status;
    private Instant createdAt;

    public LoanProductResponseDTO(UUID id, ProductStatus status, Instant createdAt) {
        this.id = id;
        this.status = status;
        this.createdAt = createdAt;
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public ProductStatus getStatus() {
        return status;
    }

    public void setStatus(ProductStatus status) {
        this.status = status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }
}
