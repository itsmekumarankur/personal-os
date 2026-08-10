# /course-tracker — Track Progress Across All Courses

View and update progress across all active Udemy and other courses.

## Modes

- `/course-tracker` — Show the full course board
- `/course-tracker update` — Report progress on one or more courses
- `/course-tracker done <course-name>` — Mark a course complete
- `/course-tracker next` — What should I study next?

## Default View (/course-tracker)

Read `vault/courses/tracker.md`. Display as a clean table:

```
ACTIVE COURSES
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Course                                  Progress
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Course Name]                           [section/total or %]
...

QUEUED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Course Name]                           Queued

COMPLETED
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[Course Name]                           Completed [Date]
```

## Update Mode (/course-tracker update)

Ask: "Which course and what section did you finish?"
Wait. Update `vault/courses/tracker.md` with the new progress.
If it's a new course not yet in the tracker, add it.
Append to `vault/log.md`.

## Next Mode (/course-tracker next)

Read:
- `vault/me/goals.md` — current priorities
- `vault/courses/tracker.md` — active course progress
- `vault/learning/` domain indexes — current knowledge state

Recommend what to study next, with reasoning. One primary recommendation.

Format: "Based on where you are with [X] and your goal to [Y], I'd focus on [recommendation]. Here's why: [2-3 sentences]."

## Vault Update (after any update)

- Update `vault/courses/tracker.md`
- If course completed, update `vault/learning/{domain}/index.md` to note completion
- Append to `vault/log.md`
