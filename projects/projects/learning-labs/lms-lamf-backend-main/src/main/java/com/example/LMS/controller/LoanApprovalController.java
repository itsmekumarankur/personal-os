package com.example.LMS.controller;

import com.example.LMS.dto.LoanApplicationResponseDTO;
import com.example.LMS.dto.LoanResponseDTO;
import com.example.LMS.entity.Loan;
import com.example.LMS.service.LoanService;
import com.example.LMS.utils.common.ApiResponse;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.UUID;

@RestController
@RequestMapping("/api/admin/loan-applications")
public class LoanApprovalController {

    private final LoanService loanService;

    public LoanApprovalController(LoanService loanService) {
        this.loanService = loanService;
    }

    @PostMapping("/{id}/approve")
    public ApiResponse<LoanResponseDTO> approve(@PathVariable UUID id) {

        Loan loan = loanService.approve(id);
        return new ApiResponse<>(true,
                new LoanResponseDTO(loan.getId(), loan.getStatus()),
                "Loan created");
    }
}