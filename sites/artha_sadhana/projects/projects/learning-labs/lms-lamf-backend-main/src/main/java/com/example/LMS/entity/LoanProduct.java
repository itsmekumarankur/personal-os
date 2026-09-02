package com.example.LMS.entity;

import com.example.LMS.utils.enumhelper.MfCategory;
import com.example.LMS.utils.enumhelper.ProductStatus;
import jakarta.persistence.*;

import java.math.BigDecimal;
import java.time.Instant;
import java.util.Set;
import java.util.UUID;

@Entity
@Table(
        name = "loan_products",
        indexes = {
                @Index(
                        name = "idx_loan_products_status_updated_at",
                        columnList = "status, updated_at DESC"
                )
        }
)
public class LoanProduct {

    @Id
    @GeneratedValue
    private UUID id;

    @Column(nullable = false, unique = true)
    private String name;

    @Column(nullable = false)
    private BigDecimal interestRate;

    @Column(nullable = false)
    private BigDecimal maxLtv;

    @Column(nullable = false)
    private BigDecimal marginCallLtv;

    @Column(nullable = false)
    private BigDecimal liquidationLtv;

    @ElementCollection(fetch = FetchType.EAGER)
    @Enumerated(EnumType.STRING)
    @CollectionTable(
            name = "loan_product_allowed_mf_categories",
            joinColumns = @JoinColumn(name = "loan_product_id")
    )
    @Column(name = "mf_category")
    private Set<MfCategory> allowedMfCategories;

    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private ProductStatus status;

    @Column(nullable = false, updatable = false)
    private Instant createdAt;

    @Column(nullable = false)
    private Instant updatedAt;

    @PrePersist
    void onCreate() {
        createdAt = Instant.now();
        updatedAt = createdAt;
        status = ProductStatus.ACTIVE;
    }

    @PreUpdate
    void onUpdate() {
        updatedAt = Instant.now();
    }

    public UUID getId() {
        return id;
    }

    public void setId(UUID id) {
        this.id = id;
    }

    public String getName() {
        return name;
    }

    public void setName(String name) {
        this.name = name;
    }

    public BigDecimal getInterestRate() {
        return interestRate;
    }

    public void setInterestRate(BigDecimal interestRate) {
        this.interestRate = interestRate;
    }

    public BigDecimal getMaxLtv() {
        return maxLtv;
    }

    public void setMaxLtv(BigDecimal maxLtv) {
        this.maxLtv = maxLtv;
    }

    public BigDecimal getMarginCallLtv() {
        return marginCallLtv;
    }

    public void setMarginCallLtv(BigDecimal marginCallLtv) {
        this.marginCallLtv = marginCallLtv;
    }

    public BigDecimal getLiquidationLtv() {
        return liquidationLtv;
    }

    public void setLiquidationLtv(BigDecimal liquidationLtv) {
        this.liquidationLtv = liquidationLtv;
    }

    public Set<MfCategory> getAllowedMfCategories() {
        return allowedMfCategories;
    }

    public void setAllowedMfCategories(Set<MfCategory> allowedMfCategories) {
        this.allowedMfCategories = allowedMfCategories;
    }

    public ProductStatus getStatus() {
        return status;
    }

    public void setStatus(ProductStatus status) {
        this.status = status;
    }

    public Instant getCreatedAt() {
        return createdAt;
    }

    public void setCreatedAt(Instant createdAt) {
        this.createdAt = createdAt;
    }

    public Instant getUpdatedAt() {
        return updatedAt;
    }

    public void setUpdatedAt(Instant updatedAt) {
        this.updatedAt = updatedAt;
    }
}
