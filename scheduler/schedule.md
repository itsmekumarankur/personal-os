# Schedule Configuration

Managed by `/cron-setup`. Edit here then run `/cron-setup` to apply.

## Active Schedules

| Command | Cron Expression | Human Readable | Status |
|---------|----------------|----------------|--------|
| /study-brief | `30 7 * * 1-5` | Weekdays 7:30 AM | ⏸️ Inactive (run /cron-setup to activate) |
| /reflect | `0 21 * * *` | Daily 9:00 PM | ⏸️ Inactive |
| /weekly-report | `0 18 * * 5` | Fridays 6:00 PM | ⏸️ Inactive |

## Instructions

Run `/cron-setup` to activate these schedules on your system.
Remove a row from this table and run `/cron-setup` to deactivate a schedule.
Change the cron expression and run `/cron-setup` to reschedule.
