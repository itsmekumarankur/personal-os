package com.example.LMS.service;

import com.example.LMS.dto.CreateLoanProductRequestDTO;
import com.example.LMS.dto.LoanProductSummaryResponseDTO;
import com.example.LMS.entity.Loan;
import com.example.LMS.entity.LoanProduct;
import com.example.LMS.exception.InvalidLoanProductException;
import com.example.LMS.exception.ResourceNotFoundException;
import com.example.LMS.repository.LoanProductRepository;
import com.example.LMS.utils.enumhelper.ProductStatus;
import org.springframework.stereotype.Service;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Service
public class LoanProductService {
    private final LoanProductRepository repository;

    public LoanProductService(LoanProductRepository repository) {
        this.repository = repository;
    }

    public LoanProduct create(CreateLoanProductRequestDTO request) {
        validate(request);

        LoanProduct product = toEntity(request);
        return repository.save(product);
    }

    public List<LoanProduct> getAll() {
        return repository.findAll();
    }

    public List<LoanProduct> getActive() {
        return repository.findByStatusOrderByUpdatedAtDesc(ProductStatus.ACTIVE);
    }

    public void updateStatus(UUID id, ProductStatus status) {
        LoanProduct product = repository.findById(id)
                .orElseThrow(() -> new ResourceNotFoundException("Loan product not found"));

        product.setStatus(status);
        repository.save(product);
    }

    public LoanProductSummaryResponseDTO getLoanProductById(UUID productId) {
        LoanProduct product =  repository.findById(productId)
                .orElseThrow(() -> new ResourceNotFoundException("Loan product not found"));

        return new LoanProductSummaryResponseDTO(
                product.getId(),
                product.getName(),
                product.getInterestRate(),
                product.getMaxLtv(),
                product.getStatus(),
                product.getAllowedMfCategories()
        );
    }

    private void validate(CreateLoanProductRequestDTO req) {

        if (req.getInterestRate() == null || req.getInterestRate().compareTo(BigDecimal.ZERO) <= 0)
            throw new InvalidLoanProductException("Interest rate must be > 0");

        if (!(req.getMaxLtv().compareTo(req.getMarginCallLtv()) < 0 && req.getMarginCallLtv().compareTo(req.getLiquidationLtv()) < 0))
            throw new InvalidLoanProductException("LTV rule violated: maxLtv < marginCallLtv < liquidationLtv");

        if (req.getAllowedMfCategories() == null || req.getAllowedMfCategories().isEmpty())
            throw new InvalidLoanProductException("MF categories required");
    }

    private LoanProduct toEntity(CreateLoanProductRequestDTO req) {
        LoanProduct p = new LoanProduct();
        p.setName(req.getName());
        p.setInterestRate(req.getInterestRate());
        p.setMaxLtv(req.getMaxLtv());
        p.setMarginCallLtv(req.getMarginCallLtv());
        p.setLiquidationLtv(req.getLiquidationLtv());
        p.setAllowedMfCategories(req.getAllowedMfCategories());
        return p;
    }
}
