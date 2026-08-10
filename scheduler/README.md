# Scheduler

This folder holds the schedule configuration for automated commands.

## How Scheduling Works

1. Add entries to `schedule.md` (manually or via `/cron-setup`)
2. Run `/cron-setup` to create systemd timer units for each schedule
3. The timer runs `claude -p "Run /{command}"` in the `personal-os_byMe/` directory

## Files

- `schedule.md` — The schedule configuration (source of truth)
- Run `/cron-setup` to apply changes to actual system timers

## Managing Schedules

```
/cron-setup          — View and configure all schedules
/cron-setup off      — Pause all schedules
/cron-setup on       — Resume all schedules
```
