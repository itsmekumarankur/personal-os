package com.example.LMS.service;

import com.example.LMS.entity.Loan;
import com.example.LMS.entity.LoanApplication;
import com.example.LMS.entity.LoanProduct;
import com.example.LMS.exception.BusinessException;
import com.example.LMS.exception.ResourceNotFoundException;
import com.example.LMS.repository.LoanApplicationMFRepository;
import com.example.LMS.repository.LoanApplicationRepository;
import com.example.LMS.repository.LoanProductRepository;
import com.example.LMS.repository.LoanRepository;
import com.example.LMS.utils.enumhelper.ApplicationStatus;
import jakarta.transaction.Transactional;
import org.springframework.stereotype.Service;

import java.util.UUID;

@Service
public class LoanService {
    private final LoanApplicationRepository appRepo;
    private final LoanRepository loanRepo;
    private final LoanApplicationMFRepository mfRepo;
    private final CollateralService collateralService;
    private final LoanProductRepository productRepo;

    public LoanService(LoanApplicationRepository appRepo, LoanRepository loanRepo, LoanApplicationMFRepository mfRepo, CollateralService collateralService, LoanProductRepository productRepo) {
        this.appRepo = appRepo;
        this.loanRepo = loanRepo;
        this.mfRepo = mfRepo;
        this.collateralService = collateralService;
        this.productRepo = productRepo;
    }

    @Transactional
    public Loan approve(UUID applicationId) {

        LoanApplication app = appRepo.findById(applicationId)
                .orElseThrow(() -> new ResourceNotFoundException("Application not found"));

        if (app.getStatus() != ApplicationStatus.VALIDATED)
            throw new BusinessException("Application not eligible");

        LoanProduct product = productRepo.findById(app.getLoanProductId()).get();
        System.out.println("product: " + product);

        Loan loan = new Loan();
        loan.setApplicationId(app.getId());
        loan.setPrincipalAmount(app.getRequestedAmount());
        loan.setLoanProductId(app.getLoanProductId());
        loan.setInterestRate(product.getInterestRate());
        loan.setOutstandingAmount(app.getRequestedAmount());
        loanRepo.save(loan);

        collateralService.createCollateral(loan.getId(), app.getId());

        app.setStatus(ApplicationStatus.APPROVED);
        appRepo.save(app);

        return loan;
    }
}
