package com.example.LMS.controller;

import com.example.LMS.dto.CollateralResponseDTO;
import com.example.LMS.dto.LoanDetailsResponseDTO;
import com.example.LMS.entity.Loan;
import com.example.LMS.service.CollateralQueryService;
import com.example.LMS.service.LoanQueryService;
import com.example.LMS.utils.common.ApiResponse;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PathVariable;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import java.util.List;
import java.util.UUID;

@RestController
@RequestMapping("/api/admin/loans")
public class LoanQueryAdminController {
    private final LoanQueryService loanQueryService;
    private final CollateralQueryService collateralQueryService;

    public LoanQueryAdminController(LoanQueryService loanQueryService, CollateralQueryService collateralQueryService) {
        this.loanQueryService = loanQueryService;
        this.collateralQueryService = collateralQueryService;
    }

    @GetMapping("/{loanId}")
    public ApiResponse<LoanDetailsResponseDTO> getLoanById(
            @PathVariable UUID loanId) {

        Loan loan = loanQueryService.getById(loanId);

        return new ApiResponse<>(
                true,
                new LoanDetailsResponseDTO(
                        loan.getId(),
                        loan.getApplicationId(),
                        loan.getLoanProductId(),
                        loan.getPrincipalAmount(),
                        loan.getOutstandingAmount(),
                        loan.getStatus(),
                        loan.getCreatedAt()
                ),
                "Loan fetched"
        );
    }

    @GetMapping("/all")
    public ApiResponse<List<LoanDetailsResponseDTO>> getAllLoans() {

        List<LoanDetailsResponseDTO> data =
                loanQueryService.getAll().stream()
                        .map(loan -> new LoanDetailsResponseDTO(
                                loan.getId(),
                                loan.getApplicationId(),
                                loan.getLoanProductId(),
                                loan.getPrincipalAmount(),
                                loan.getOutstandingAmount(),
                                loan.getStatus(),
                                loan.getCreatedAt()
                        ))
                        .toList();

        return new ApiResponse<>(true, data, "Loans fetched");
    }

    @GetMapping("/{loanId}/collaterals")
    public ApiResponse<List<CollateralResponseDTO>> getCollateralsByLoanId(
            @PathVariable UUID loanId) {

        List<CollateralResponseDTO> data =
                collateralQueryService.getByLoanId(loanId).stream()
                        .map(c -> new CollateralResponseDTO(
                                c.getId(),
                                c.getIsin(),
                                c.getUnits(),
                                c.getNav(),
                                c.getCollateralValue(),
                                c.getStatus()
                        ))
                        .toList();

        return new ApiResponse<>(true, data, "Collaterals fetched");
    }
}
