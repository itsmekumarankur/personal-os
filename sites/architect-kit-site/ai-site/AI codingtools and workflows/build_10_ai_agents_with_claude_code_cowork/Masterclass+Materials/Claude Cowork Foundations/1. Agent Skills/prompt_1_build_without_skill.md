# Prompt 1: Create a Sales Presentation (Without Skill)

> **Instructor note:** Before running this prompt, make sure no presentation or PPT-related skills are installed in Cowork. Go to Settings > Customize > Skills and confirm none are active. Upload the `quarterly_sales.csv` file from the `datasets/` folder into the Cowork conversation.

Copy and paste the following into Cowork:

```
Context: I have a CSV file with quarterly sales data for NovaTech Solutions, a SaaS company. The data covers all of 2025 across 3 regions (North America, Europe, Asia Pacific) and 2 product lines (Cloud Services, Consulting). Each row has the month, quarter, region, product line, revenue, units sold, and target. I need to present this to the C-suite at our annual review.

Instruction: Create an executive presentation from this data. This deck will be presented by the VP of Sales to the C-suite. Do not use any ppt skills (very important)

Input:
- Data source: quarterly_sales.csv (uploaded to this conversation)
- Company: NovaTech Solutions
- Audience: C-suite executives
- Tone: Confident, data-driven, forward-looking

Output:
- A file called novatech_annual_review.pptx
```

> **Instructor note:** Without the PPT skill, Cowork will produce basic slides: bullet-heavy, default fonts, charts dumped without context, no visual hierarchy, every slide looks the same, walls of text. This is the "before" for comparison. Keep the file or take screenshots for the side-by-side.
