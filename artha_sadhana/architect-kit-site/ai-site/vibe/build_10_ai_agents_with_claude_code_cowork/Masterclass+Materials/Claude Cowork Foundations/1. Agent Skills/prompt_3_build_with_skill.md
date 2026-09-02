# Prompt 3: Create a Sales Presentation (With Skill)

> **Instructor note:** The ppt-visual skill should now be installed and active. Start a **NEW Cowork conversation** (do not continue the old one). This is important so the skill is picked up fresh. Upload the same `quarterly_sales.csv` file again.

Copy and paste the following into a new Cowork session:

```
Context: I have a CSV file with quarterly sales data for NovaTech Solutions, a SaaS company. The data covers all of 2025 across 3 regions (North America, Europe, Asia Pacific) and 2 product lines (Cloud Services, Consulting). Each row has the month, quarter, region, product line, revenue, units sold, and target. I need to present this to the C-suite at our annual review.

Instruction: Create a executive presentation from this data. This deck will be presented by the VP of Sales to the C-suite. Use the /ppt-visual skill to design the presentation. Use all available PPT skills you have to make this the best possible presentation. Make it next level. 

Input:
- Data source: quarterly_sales.csv (uploaded to this conversation)
- Company: NovaTech Solutions
- Audience: C-suite executives
- Tone: Confident, data-driven, forward-looking

Output:
- A file called novatech_annual_review_v2.pptx
```

> **Instructor note:** Two key differences from Prompt 1:
> 1. This runs in a **new session** with the ppt-visual skill active
> 2. The output file is named **novatech_annual_review_v2.pptx** so students can compare both files side by side
>
> **Without skill (v1):** Bullet-heavy slides, default fonts, charts dumped without context, no visual hierarchy, every slide looks the same, walls of text.
>
> **With skill (v2):** Each slide has one clear message, big hero numbers, proper layout (split layouts, data highlight patterns), consistent typography pairing, intentional color palette, whitespace, charts with callout annotations, designed infographic feel.
>
> Open both files side by side: v1 (without skill) and v2 (with skill). The visual gap should be immediately obvious. This is the moment students understand what a skill does.
