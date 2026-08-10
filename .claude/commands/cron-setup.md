# /cron-setup — Manage Scheduled Commands

Set up, view, or remove automated schedules for commands that should run on a recurring basis.

## Step 1: Read Schedule

Read `scheduler/schedule.md` to see what's currently configured.

## Step 2: Ask What to Configure

If the user hasn't said: "Which commands do you want to run automatically, and when?"

Common schedule for a learner:
- `/study-brief` — Every weekday morning (e.g., 7:30 AM)
- `/reflect` — Every evening (e.g., 9:00 PM)
- `/weekly-report` — Every Friday (e.g., 6:00 PM)
- `/career-radar` — Every 4 weeks

## Step 3: Update scheduler/schedule.md

Add or update entries:

```markdown
## Active Schedules

| Command | Schedule (cron) | Human Readable |
|---------|----------------|----------------|
| /study-brief | 30 7 * * 1-5 | Weekdays 7:30 AM |
| /reflect | 0 21 * * * | Daily 9:00 PM |
| /weekly-report | 0 18 * * 5 | Fridays 6:00 PM |
| /career-radar | 0 10 1 * * | 1st of every month |
```

## Step 4: Create System Jobs (Linux/systemd)

For each active schedule, create a systemd timer unit:

```bash
# Create service file
cat > ~/.config/systemd/user/personal-os-{name}.service << EOF
[Unit]
Description=Personal OS: /{command}

[Service]
Type=oneshot
ExecStart=/usr/bin/claude -p "Run /{command}" --cwd /home/isha/Desktop/CODE/personal-os_byMe
EOF

# Create timer file
cat > ~/.config/systemd/user/personal-os-{name}.timer << EOF
[Unit]
Description=Personal OS: /{command} timer

[Timer]
OnCalendar={systemd-calendar-format}
Persistent=true

[Install]
WantedBy=timers.target
EOF

# Enable and start
systemctl --user enable personal-os-{name}.timer
systemctl --user start personal-os-{name}.timer
```

Convert cron syntax to systemd OnCalendar format:
- `30 7 * * 1-5` → `Mon-Fri 07:30:00`
- `0 21 * * *` → `*-*-* 21:00:00`
- `0 18 * * 5` → `Fri 18:00:00`

## Step 5: Confirm

List what was set up:
```
Scheduled:
  /study-brief  — Weekdays 7:30 AM  [active]
  /reflect      — Daily 9:00 PM     [active]
  /weekly-report — Fridays 6:00 PM  [active]
```

## To Remove a Schedule

```bash
systemctl --user stop personal-os-{name}.timer
systemctl --user disable personal-os-{name}.timer
rm ~/.config/systemd/user/personal-os-{name}.*
```

Then update `scheduler/schedule.md` to remove the entry.
