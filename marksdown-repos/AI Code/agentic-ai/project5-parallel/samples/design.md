# Design: Customer Report Export Service

Users click "Export" in the web app and receive a CSV of their last 12 months of
transactions by email.

- A single API server (one VM) receives the request, queries the primary Postgres
  database directly with a full-table scan filtered by user id, builds the CSV in
  memory, and sends it by email in the same HTTP request.
- The API key for the email provider is stored in a config file in the git repository.
- The export link in the email is a public URL containing the numeric user id.
- There is no retry if the email provider is down; the user sees an error and tries again.
- The VM is sized for peak month-end traffic and runs all month.
- Logging is print statements to the console.
