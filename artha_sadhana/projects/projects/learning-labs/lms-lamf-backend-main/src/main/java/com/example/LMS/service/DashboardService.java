package com.example.LMS.service;

import com.example.LMS.dto.DashboardSummaryResponseDTO;
import com.example.LMS.repository.LoanApplicationRepository;
import com.example.LMS.repository.LoanProductRepository;
import com.example.LMS.repository.LoanRepository;
import com.example.LMS.utils.enumhelper.ApplicationStatus;
import com.example.LMS.utils.enumhelper.LoanStatus;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.Map;
import java.util.stream.Collectors;

@Service
public class DashboardService {

    private final LoanApplicationRepository applicationRepo;
    private final LoanRepository loanRepo;
    private final LoanProductRepository productRepo;

    public DashboardService(
            LoanApplicationRepository applicationRepo,
            LoanRepository loanRepo,
            LoanProductRepository productRepo
    ) {
        this.applicationRepo = applicationRepo;
        this.loanRepo = loanRepo;
        this.productRepo = productRepo;
    }

    public DashboardSummaryResponseDTO getSummary() {

        // ---- Application metrics ----
        long totalApplications = applicationRepo.count();
        long approvedApplications =
                applicationRepo.countByStatus(ApplicationStatus.APPROVED);

        Map<String, Long> applicationBreakdown =
                applicationRepo.countByStatusGroup().stream()
                        .collect(Collectors.toMap(
                                r -> r[0].toString(),
                                r -> (Long) r[1]
                        ));

        // ---- Loan metrics ----
        long totalLoans = loanRepo.count();
        BigDecimal totalOutstanding = loanRepo.totalOutstanding();

        String formattedOutstanding =
                formatAmount(totalOutstanding);

        long activeLoans = loanRepo.countByStatus(LoanStatus.ACTIVE);
        long marginCallLoans = loanRepo.countByStatus(LoanStatus.MARGIN_CALL);
        long liquidationLoans =
                loanRepo.countByStatus(LoanStatus.LIQUIDATION_TRIGGERED);

        // ---- Product metrics ----
        BigDecimal averageMaxLtv =
                productRepo.averageMaxLtv()
                        .setScale(2, RoundingMode.HALF_UP);

        return new DashboardSummaryResponseDTO(
                totalApplications,
                approvedApplications,
                applicationBreakdown,
                totalLoans,
                totalOutstanding,
                formattedOutstanding,
                activeLoans,
                marginCallLoans,
                liquidationLoans,
                averageMaxLtv
        );
    }

    private String formatAmount(BigDecimal amount) {

        BigDecimal crore = new BigDecimal("10000000");
        BigDecimal lakh = new BigDecimal("100000");

        if (amount.compareTo(crore) >= 0) {
            return amount.divide(crore, 2, RoundingMode.HALF_UP) + " Cr";
        }
        if (amount.compareTo(lakh) >= 0) {
            return amount.divide(lakh, 2, RoundingMode.HALF_UP) + " L";
        }
        return amount + "";
    }
}
