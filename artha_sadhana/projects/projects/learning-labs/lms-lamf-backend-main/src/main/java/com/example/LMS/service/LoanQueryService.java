package com.example.LMS.service;

import com.example.LMS.entity.Loan;
import com.example.LMS.exception.ResourceNotFoundException;
import com.example.LMS.repository.LoanRepository;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.UUID;

@Service
public class LoanQueryService {
    private final LoanRepository loanRepo;

    public LoanQueryService(LoanRepository loanRepo) {
        this.loanRepo = loanRepo;
    }

    public Loan getById(UUID loanId) {
        return loanRepo.findById(loanId)
                .orElseThrow(() ->
                        new ResourceNotFoundException("Loan not found"));
    }

    public List<Loan> getAll() {
        return loanRepo.findAll();
    }
}
