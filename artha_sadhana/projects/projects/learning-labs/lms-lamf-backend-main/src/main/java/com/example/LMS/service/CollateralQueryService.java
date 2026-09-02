package com.example.LMS.service;

import com.example.LMS.entity.Collateral;
import com.example.LMS.repository.CollateralRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
public class CollateralQueryService {

    private final CollateralRepository collateralRepo;

    public CollateralQueryService(CollateralRepository collateralRepo) {
        this.collateralRepo = collateralRepo;
    }

    public List<Collateral> getByLoanId(UUID loanId) {
        return collateralRepo.findByLoanId(loanId);
    }
}
