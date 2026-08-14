package com.example.LMS.controller;

import com.example.LMS.dto.CreateLoanProductRequestDTO;
import com.example.LMS.dto.LoanProductResponseDTO;
import com.example.LMS.dto.LoanProductSummaryResponseDTO;
import com.example.LMS.dto.UpdateLoanProductStatusRequestDTO;
import com.example.LMS.entity.LoanProduct;
import com.example.LMS.service.LoanProductService;
import com.example.LMS.utils.common.ApiResponse;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/admin/loan-products")
public class LoanProductController {
    private final LoanProductService productService;

    public LoanProductController(LoanProductService service) {
        this.productService = service;
    }


    @PostMapping
    public ApiResponse<LoanProductResponseDTO> create(@RequestBody CreateLoanProductRequestDTO request) {

        LoanProduct p = productService.create(request);

        LoanProductResponseDTO response = new LoanProductResponseDTO(p.getId(), p.getStatus(), p.getCreatedAt());

        return new ApiResponse<>(true, response, "Loan product created successfully");
    }


    @GetMapping("/all")
    public ApiResponse<List<LoanProductSummaryResponseDTO>> getAll() {

        List<LoanProductSummaryResponseDTO> data = productService.getAll().stream().map(this::toSummary).toList();

        return new ApiResponse<>(true, data, "Loan products fetched successfully");
    }


    @GetMapping
    public ApiResponse<List<LoanProductSummaryResponseDTO>> getActive() {

            List<LoanProductSummaryResponseDTO> data = productService.getActive().stream().map(this::toSummary).toList();

        return new ApiResponse<>(true, data, "Active loan products fetched successfully");
    }

    @GetMapping("/{id}")
    public ApiResponse<LoanProductSummaryResponseDTO> getLoanProductById(@PathVariable UUID id) {

        LoanProductSummaryResponseDTO data = productService.getLoanProductById(id);

        return new ApiResponse<LoanProductSummaryResponseDTO>(true, data, "Loan product fetched successfully");
    }


    @PatchMapping("/{id}/status")
    public ApiResponse<Void> updateStatus(@PathVariable UUID id, @RequestBody UpdateLoanProductStatusRequestDTO request) {

        productService.updateStatus(id, request.getStatus());

        return new ApiResponse<>(true, null, "Loan product status updated successfully");
    }

    private LoanProductSummaryResponseDTO toSummary(LoanProduct p) {
        return new LoanProductSummaryResponseDTO(
                p.getId(),
                p.getName(),
                p.getInterestRate(),
                p.getMaxLtv(),
                p.getStatus(),
                p.getAllowedMfCategories()
        );
    }
}
