package com.example.LMS.controller;

import com.example.LMS.dto.CreateLoanApplicationRequestDTO;
import com.example.LMS.dto.LoanApplicationResponseDTO;
import com.example.LMS.entity.LoanApplication;
import com.example.LMS.service.LoanApplicationService;
import com.example.LMS.utils.common.ApiResponse;
import jakarta.validation.Valid;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/loan-applications")
public class LoanApplicationController {
    private final LoanApplicationService service;

    public LoanApplicationController(LoanApplicationService service) {
        this.service = service;
    }

    @PostMapping
    public ApiResponse<LoanApplicationResponseDTO> create(
            @Valid @RequestBody CreateLoanApplicationRequestDTO req) {

        LoanApplication app = service.createAndValidate(req);

        return new ApiResponse<>(true,
                new LoanApplicationResponseDTO(app.getId(), app.getStatus(), null),
                "Application processed");
    }
}
