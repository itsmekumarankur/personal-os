package com.example.LMS.controller;

import com.example.LMS.dto.DashboardSummaryResponseDTO;
import com.example.LMS.service.DashboardService;
import com.example.LMS.utils.common.ApiResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/admin/dashboard")
public class DashboardController {

    private final DashboardService service;

    public DashboardController(DashboardService service) {
        this.service = service;
    }

    @GetMapping("/summary")
    public ApiResponse<DashboardSummaryResponseDTO> getSummary() {

        return new ApiResponse<>(
                true,
                service.getSummary(),
                "Dashboard summary fetched"
        );
    }
}
