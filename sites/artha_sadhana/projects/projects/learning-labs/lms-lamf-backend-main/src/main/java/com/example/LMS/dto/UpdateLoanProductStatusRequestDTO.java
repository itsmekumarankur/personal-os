package com.example.LMS.dto;

import com.example.LMS.utils.enumhelper.ProductStatus;

public class UpdateLoanProductStatusRequestDTO {
    private ProductStatus status;

    public ProductStatus getStatus() {
        return status;
    }

    public void setStatus(ProductStatus status) {
        this.status = status;
    }
}
