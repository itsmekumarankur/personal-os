package com.example.LMS.repository;

import com.example.LMS.entity.Collateral;
import com.example.LMS.utils.enumhelper.CollateralStatus;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface CollateralRepository extends JpaRepository<Collateral, UUID> {
    boolean existsByIsinAndStatus(String isin, CollateralStatus status);
    List<Collateral> findByLoanId(UUID loanId);
}
