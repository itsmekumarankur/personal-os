Plan the move of our monthly interest-calculation batch job from one cron server to an
event-driven design on AWS.

Facts:
- About 2 million customer accounts; the job runs for 5 hours on the 1st of each month.
- It must never charge or credit the same account twice, even if a step is retried.
- The finance team needs an audit trail for every calculation.
- The team has 4 engineers and 8 weeks.
