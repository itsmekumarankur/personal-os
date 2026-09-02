package com.example.LMS.repository;

import com.example.LMS.entity.Loan;
import com.example.LMS.utils.enumhelper.LoanStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;

import java.math.BigDecimal;
import java.util.UUID;

public interface LoanRepository extends JpaRepository<Loan, UUID> {
    long countByStatus(LoanStatus status);

    @Query("SELECT COALESCE(SUM(l.outstandingAmount), 0) FROM Loan l")
    BigDecimal totalOutstanding();

}
