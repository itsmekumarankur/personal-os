package com.example.LMS.controller;

import com.example.LMS.dto.LoanApplicationDetailsResponseDTO;
import com.example.LMS.dto.LoanApplicationResponseDTO;
import com.example.LMS.entity.LoanApplication;
import com.example.LMS.service.LoanApplicationService;
import com.example.LMS.utils.common.ApiResponse;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/admin/loan-applications")
public class LoanApplicationAdminController {

    private final LoanApplicationService service;

    public LoanApplicationAdminController(LoanApplicationService service) {
        this.service = service;
    }

    @GetMapping
    public ApiResponse<List<LoanApplicationDetailsResponseDTO>> getAll() {

        List<LoanApplicationDetailsResponseDTO> data =
                service.getAll().stream()
                        .map(app -> new LoanApplicationDetailsResponseDTO(
                                app.getId(),
                                app.getCustomerId(),
                                app.getLoanProductId(),
                                app.getRequestedAmount(),
                                app.getEligibleAmount(),
                                app.getStatus()
                        ))
                        .toList();

        return new ApiResponse<>(true, data, "Applications fetched");
    }

    @GetMapping("/{id}")
    public ApiResponse<LoanApplicationDetailsResponseDTO> getById(@PathVariable UUID id) {

        LoanApplication app = service.getById(id);

        return new ApiResponse<>(
                true,
                new LoanApplicationDetailsResponseDTO(
                        app.getId(),
                        app.getCustomerId(),
                        app.getLoanProductId(),
                        app.getRequestedAmount(),
                        app.getEligibleAmount(),
                        app.getStatus()
                ),
                "Application fetched"
        );
    }
}

