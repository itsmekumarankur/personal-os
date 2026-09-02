package com.example.LMS.dto;

import java.math.BigDecimal;
import java.util.Map;

public class DashboardSummaryResponseDTO {

    // Application metrics
    private long totalApplications;
    private long approvedApplications;
    private Map<String, Long> applicationStatusBreakdown;

    // Loan metrics
    private long totalLoans;
    private BigDecimal totalOutstanding;
    private String totalOutstandingFormatted;

    // Risk metrics
    private long activeLoans;
    private long marginCallLoans;
    private long liquidationLoans;

    // Product metrics
    private BigDecimal averageMaxLtv;

    public DashboardSummaryResponseDTO(
            long totalApplications,
            long approvedApplications,
            Map<String, Long> applicationStatusBreakdown,
            long totalLoans,
            BigDecimal totalOutstanding,
            String totalOutstandingFormatted,
            long activeLoans,
            long marginCallLoans,
            long liquidationLoans,
            BigDecimal averageMaxLtv
    ) {
        this.totalApplications = totalApplications;
        this.approvedApplications = approvedApplications;
        this.applicationStatusBreakdown = applicationStatusBreakdown;
        this.totalLoans = totalLoans;
        this.totalOutstanding = totalOutstanding;
        this.totalOutstandingFormatted = totalOutstandingFormatted;
        this.activeLoans = activeLoans;
        this.marginCallLoans = marginCallLoans;
        this.liquidationLoans = liquidationLoans;
        this.averageMaxLtv = averageMaxLtv;
    }

    public long getTotalApplications() {
        return totalApplications;
    }

    public long getApprovedApplications() {
        return approvedApplications;
    }

    public Map<String, Long> getApplicationStatusBreakdown() {
        return applicationStatusBreakdown;
    }

    public long getTotalLoans() {
        return totalLoans;
    }

    public BigDecimal getTotalOutstanding() {
        return totalOutstanding;
    }

    public String getTotalOutstandingFormatted() {
        return totalOutstandingFormatted;
    }

    public long getActiveLoans() {
        return activeLoans;
    }

    public long getMarginCallLoans() {
        return marginCallLoans;
    }

    public long getLiquidationLoans() {
        return liquidationLoans;
    }

    public BigDecimal getAverageMaxLtv() {
        return averageMaxLtv;
    }
}