# Prompt 4: Create a Custom Cowork Command

> **Instructor note:** Continue in the same Cowork conversation. Now we turn the 3-step Apple workflow into a reusable command.

Copy and paste the following into Cowork:

```
Context: We just built a 3-step workflow in this conversation: (1) search for Apple performance, sentiment, and news, (2) organize it into an Excel tracker, and (3) create a PowerPoint update deck. I want to turn this into a single reusable command so I can monitor Apple with one word.

Instruction: Create a Cowork command called /apple-monitor that chains all three steps together automatically. When I run /apple-monitor, it should do the full workflow end to end.

Input:
- Step 1: Search online for latest AAPL performance (price, change, metrics, analyst sentiment, social sentiment, news) plus SPY and QQQ benchmarks
- Step 2: Organize into apple_monitor.xlsx (dashboard with chart, fundamentals, sentiment, news sheets)
- Step 3: Create apple_update.pptx (6 slides: title, price snapshot, analyst sentiment, social sentiment, news, overall assessment)

Output:
- A working Cowork command called /apple-monitor
- When I type /apple-monitor in a new conversation, all three steps run automatically
- Confirm the command is created and ready to use
```

> **Instructor note:** Once done, test it by typing /apple-monitor in a new conversation. Explain that they can modify this for any stock they care about. The command is theirs to customize.
