package com.example.LMS.repository;

import com.example.LMS.entity.LoanApplication;
import com.example.LMS.utils.enumhelper.ApplicationStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.util.List;
import java.util.UUID;

public interface LoanApplicationRepository extends JpaRepository<LoanApplication, UUID> {
    long countByStatus(ApplicationStatus status);

    @Query("""
        SELECT la.status, COUNT(la)
        FROM LoanApplication la
        GROUP BY la.status
    """)
    List<Object[]> countByStatusGroup();
}
