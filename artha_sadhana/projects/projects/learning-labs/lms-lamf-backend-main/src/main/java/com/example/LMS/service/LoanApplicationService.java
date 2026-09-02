package com.example.LMS.service;

import com.example.LMS.dto.CreateLoanApplicationRequestDTO;
import com.example.LMS.dto.MutualFundRequestDTO;
import com.example.LMS.entity.LoanApplication;
import com.example.LMS.entity.LoanApplicationMF;
import com.example.LMS.entity.LoanProduct;
import com.example.LMS.exception.BusinessException;
import com.example.LMS.exception.InvalidApplicationStateException;
import com.example.LMS.exception.InvalidLoanProductException;
import com.example.LMS.exception.ResourceNotFoundException;
import com.example.LMS.repository.CollateralRepository;
import com.example.LMS.repository.LoanApplicationMFRepository;
import com.example.LMS.repository.LoanApplicationRepository;
import com.example.LMS.repository.LoanProductRepository;
import com.example.LMS.utils.enumhelper.ApplicationStatus;
import com.example.LMS.utils.enumhelper.CollateralStatus;
import com.example.LMS.utils.enumhelper.ProductStatus;
import jakarta.transaction.Transactional;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Service
public class LoanApplicationService {
    private final LoanApplicationRepository appRepo;
    private final LoanApplicationMFRepository mfRepo;
    private final CollateralRepository collateralRepo;
    private final LoanProductRepository productRepo;

    public LoanApplicationService(LoanApplicationRepository appRepo, LoanApplicationMFRepository mfRepo, CollateralRepository collateralRepo, LoanProductRepository productRepo) {
        this.appRepo = appRepo;
        this.mfRepo = mfRepo;
        this.collateralRepo = collateralRepo;
        this.productRepo = productRepo;
    }

    @Transactional
    public LoanApplication createAndValidate(CreateLoanApplicationRequestDTO req) {

        LoanProduct product = productRepo.findById(req.getLoanProductId())
                .orElseThrow(() -> new ResourceNotFoundException("Product not found"));

        if (product.getStatus() != ProductStatus.ACTIVE)
            throw new BusinessException("Product inactive");

        for (MutualFundRequestDTO mf : req.getMutualFunds()) {

            if (mf.getUnits() == null || mf.getUnits().compareTo(BigDecimal.ZERO) <= 0) {
                throw new BusinessException("MF units must be positive");
            }

            if (collateralRepo.existsByIsinAndStatus(mf.getIsin(), CollateralStatus.PLEDGED)) {
                throw new BusinessException("MF already pledged");
            }
        }

        LoanApplication app = new LoanApplication();
        app.setCustomerId(req.getCustomerId());
        app.setLoanProductId(req.getLoanProductId());
        app.setRequestedAmount(req.getRequestedAmount());
        appRepo.save(app);

        BigDecimal collateralValue = BigDecimal.ZERO;

        for (MutualFundRequestDTO mf : req.getMutualFunds()) {

            if (collateralRepo.existsByIsinAndStatus(mf.getIsin(), CollateralStatus.PLEDGED))
                throw new BusinessException("MF already pledged");

            LoanApplicationMF snapshot = new LoanApplicationMF();
            snapshot.setApplicationId(app.getId());
            snapshot.setIsin(mf.getIsin());
            snapshot.setUnits(mf.getUnits());
            mfRepo.save(snapshot);

            BigDecimal nav = mockNav();
            collateralValue = collateralValue.add(nav.multiply(mf.getUnits()));
        }

        BigDecimal eligibleAmount = collateralValue.multiply(product.getMaxLtv());
        app.setEligibleAmount(eligibleAmount);

        app.setStatus(
                app.getRequestedAmount().compareTo(eligibleAmount) <= 0
                        ? ApplicationStatus.VALIDATED
                        : ApplicationStatus.REJECTED
        );

        return appRepo.save(app);
    }

    private BigDecimal mockNav() {
        return BigDecimal.valueOf(100);
    }

    public List<LoanApplication> getAll() {
        return appRepo.findAll();
    }

    public LoanApplication getById(UUID id) {
        return appRepo.findById(id)
                .orElseThrow(() ->
                        new ResourceNotFoundException("Application not found"));
    }
}
