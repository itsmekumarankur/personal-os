package com.example.LMS.service;

import com.example.LMS.entity.Collateral;
import com.example.LMS.entity.Loan;
import com.example.LMS.entity.LoanProduct;
import com.example.LMS.exception.ResourceNotFoundException;
import com.example.LMS.repository.CollateralRepository;
import com.example.LMS.repository.LoanProductRepository;
import com.example.LMS.repository.LoanRepository;
import com.example.LMS.utils.enumhelper.LoanStatus;
import jakarta.transaction.Transactional;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.math.RoundingMode;
import java.util.List;
import java.util.UUID;

@Service
public class LoanHealthService {
    private final LoanRepository loanRepo;
    private final CollateralRepository collateralRepo;
    private final LoanProductRepository productRepo;

    public LoanHealthService(LoanRepository loanRepo, CollateralRepository collateralRepo, LoanProductRepository productRepo) {
        this.loanRepo = loanRepo;
        this.collateralRepo = collateralRepo;
        this.productRepo = productRepo;
    }

    @Transactional
    public void updateLoanHealth(UUID loanId, BigDecimal newNav) {

        Loan loan = loanRepo.findById(loanId)
                .orElseThrow(() -> new ResourceNotFoundException("Loan not found"));

        List<Collateral> collaterals = collateralRepo.findByLoanId(loanId);

        BigDecimal totalCollateralValue = BigDecimal.ZERO;

        for (Collateral c : collaterals) {
            c.setNav(newNav);
            c.setCollateralValue(newNav.multiply(c.getUnits()));
            totalCollateralValue = totalCollateralValue.add(c.getCollateralValue());
            collateralRepo.save(c);
        }

        BigDecimal ltv =
                loan.getOutstandingAmount().divide(
                        totalCollateralValue, 4, RoundingMode.HALF_UP);

        LoanProduct product =
                productRepo.findById(loan.getLoanProductId()).get();

        if (ltv.compareTo(product.getMaxLtv()) <= 0)
            loan.setStatus(LoanStatus.ACTIVE);
        else if (ltv.compareTo(product.getMarginCallLtv()) <= 0)
            loan.setStatus(LoanStatus.MARGIN_CALL);
        else
            loan.setStatus(LoanStatus.LIQUIDATION_TRIGGERED);

        loanRepo.save(loan);
    }
}
