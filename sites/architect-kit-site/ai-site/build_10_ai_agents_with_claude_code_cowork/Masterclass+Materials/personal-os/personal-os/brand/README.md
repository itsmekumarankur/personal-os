# Brand Assets

Drop your brand materials here. The agent uses these when generating reports, decks, Excel files, and any branded output.

## images/
Put your logo and any brand images here. Supported formats: PNG, JPG, SVG.
- logo.png (or .jpg, .svg)
- Any other brand images you want in reports/decks

## templates/
Put your templates here. The agent uses these as starting points when generating files.
- PowerPoint template (.pptx) - your slide master with brand colors, fonts, layouts
- Excel template (.xlsx) - your preferred Excel format with headers, formulas, styling
- PDF template or guidelines - how you want PDFs to look

## config/
The agent creates and maintains these after you provide your brand details:
- brand-config.md - colors, fonts, tone, formatting rules (auto-generated from your inputs)
- If you don't have templates, tell the agent your brand colors and fonts and it will generate config from scratch.

## How to use
1. Drop your files in the right folders
2. Tell the agent: "update my brand config" or run /setup and it will ask about brand
3. Every automation that generates output (reports, decks, Excel, PDF) reads from here
4. To update: replace files here and tell the agent "refresh brand config"
