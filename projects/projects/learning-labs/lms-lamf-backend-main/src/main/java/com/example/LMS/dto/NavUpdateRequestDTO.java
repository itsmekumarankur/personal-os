package com.example.LMS.dto;

import jakarta.validation.constraints.NotNull;
import jakarta.validation.constraints.Positive;

import java.math.BigDecimal;

public class NavUpdateRequestDTO {
    @NotNull
    @Positive
    private BigDecimal nav;

    public BigDecimal getNav() {
        return nav;
    }

    public void setNav(BigDecimal nav) {
        this.nav = nav;
    }
}
