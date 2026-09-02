package com.example.LMS.service;

import com.example.LMS.entity.Collateral;
import com.example.LMS.entity.LoanApplicationMF;
import com.example.LMS.repository.CollateralRepository;
import com.example.LMS.repository.LoanApplicationMFRepository;
import com.example.LMS.utils.enumhelper.CollateralStatus;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Service
public class CollateralService {
    private final LoanApplicationMFRepository mfRepo;
    private final CollateralRepository collateralRepo;

    public CollateralService(LoanApplicationMFRepository mfRepo, CollateralRepository collateralRepo) {
        this.mfRepo = mfRepo;
        this.collateralRepo = collateralRepo;
    }

    public void createCollateral(UUID loanId, UUID applicationId) {

        List<LoanApplicationMF> mfs = mfRepo.findByApplicationId(applicationId);

        for (LoanApplicationMF mf : mfs) {
            BigDecimal nav = BigDecimal.valueOf(100);

            Collateral c = new Collateral();
            c.setLoanId(loanId);
            c.setIsin(mf.getIsin());
            c.setUnits(mf.getUnits());
            c.setNav(nav);
            c.setCollateralValue(nav.multiply(mf.getUnits()));
            c.setStatus(CollateralStatus.PLEDGED);

            collateralRepo.save(c);
        }

        mfRepo.deleteAll(mfs);
    }
}
