package com.example.LMS.repository;

import com.example.LMS.entity.LoanProduct;
import com.example.LMS.utils.enumhelper.ProductStatus;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.math.BigDecimal;
import java.util.List;
import java.util.UUID;

@Repository
public interface LoanProductRepository extends JpaRepository<LoanProduct, UUID> {
    List<LoanProduct> findByStatusOrderByUpdatedAtDesc(ProductStatus status);
    @Query("SELECT AVG(lp.maxLtv) FROM LoanProduct lp")
    BigDecimal averageMaxLtv();
}
