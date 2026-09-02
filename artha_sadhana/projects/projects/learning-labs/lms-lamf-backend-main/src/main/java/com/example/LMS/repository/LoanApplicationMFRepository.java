package com.example.LMS.repository;

import com.example.LMS.entity.LoanApplicationMF;
import org.springframework.data.jpa.repository.JpaRepository;

import java.util.List;
import java.util.UUID;

public interface LoanApplicationMFRepository extends JpaRepository<LoanApplicationMF, UUID> {
    List<LoanApplicationMF> findByApplicationId(UUID applicationId);
}
