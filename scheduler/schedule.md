# Schedule Configuration

Managed by `/cron-setup`. Edit here then run `/cron-setup` to apply.

## Active Schedules

| Command | Cron Expression | Human Readable | Status |
|---------|----------------|----------------|--------|
| /market-pulse | `0 7 * * *` | Daily 7:00 AM | ⏸️ Inactive (run /cron-setup to activate) |
| /morning-brief | `0 8 * * *` | Daily 8:00 AM | ⏸️ Inactive (run /cron-setup to activate) |
| /sprint-tracker | `0 9 * * 1-5` | Weekdays 9:00 AM | ⏸️ Inactive (run /cron-setup to activate) |
| /study-brief | `30 7 * * 1-5` | Weekdays 7:30 AM | ⏸️ Inactive (run /cron-setup to activate) |
| /reflect | `0 21 * * *` | Daily 9:00 PM | ⏸️ Inactive |
| /weekly-report | `0 18 * * 5` | Fridays 6:00 PM | ⏸️ Inactive |

## Instructions

Run `/cron-setup` to activate these schedules on your system.
Remove a row from this table and run `/cron-setup` to deactivate a schedule.
Change the cron expression and run `/cron-setup` to reschedule.
