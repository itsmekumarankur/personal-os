package com.example.LMS.controller;

import com.example.LMS.dto.NavUpdateRequestDTO;
import com.example.LMS.service.LoanHealthService;
import com.example.LMS.utils.common.ApiResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.*;

import java.util.UUID;

@RestController
@RequestMapping("/api/admin/loan-health")
public class LoanHealthController {

    private final LoanHealthService service;

    public LoanHealthController(LoanHealthService service) {
        this.service = service;
    }

    @PostMapping("/{loanId}/nav")
    public ApiResponse<Void> updateNav(
            @PathVariable UUID loanId,
            @Valid @RequestBody NavUpdateRequestDTO req) {

        service.updateLoanHealth(loanId, req.getNav());
        return new ApiResponse<>(true, null, "Loan health updated");
    }
}