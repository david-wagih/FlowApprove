# FlowApprove — Expense Approval & Reimbursement

A small but realistic event-driven microservices app used as the running example in the
**DevOps with David** YouTube series (Linux Fundamentals, Git Fundamentals, and more to come). This
repo holds **only the application code**, with no Dockerfiles and no docker-compose. Clone it and
follow along with the videos.

The domain is the expense workflow every company runs, whether it's an ERP finance module or a
SaaS tool like SAP Concur: an employee submits an expense claim, their manager approves or rejects
it, finance reimburses the approved ones, and the employee is kept in the loop by email at every
step. It looks tiny from the outside, but it has the shape of a real business process system — a
multi-step state machine, approvals routed along the org chart, a money-moving step that must never
pay the same claim twice, and a payment provider that sometimes fails.

## Architecture

Four independent components. The three APIs each own their own data store, and they never call
each other over HTTP: everything between services goes through RabbitMQ, and the one thing
approval-service needs from employee-service ("who is calling, and are they a manager?") comes from
the caller's JWT, verified locally.

```
                                  ┌───────────────┐
                                  │    Client     │
                                  └───────┬───────┘
                                          │ HTTP + JWT (issued by employee-service)
            ┌─────────────────────────────┼─────────────────────────────┐
            ▼                             ▼                             ▼
 ┌────────────────────┐        ┌────────────────────┐        ┌────────────────────┐
 │  employee-service  │        │  approval-service  │        │  payment-service   │
 │       :8001        │        │       :8002        │        │       :8003        │
 │     (Postgres)     │        │      (Redis)       │        │     (Postgres)     │
 └─────┬────────▲─────┘        └─────┬────────▲─────┘        └─────┬────────▲─────┘
       │        │                    │        │                    │        │
       ▼        │                    ▼        │                    ▼        │
   ┌────────────┴─────────────────────────────┴─────────────────────────────┴─────┐
   │                     expenses_exchange (RabbitMQ, topic)                      │
   └──────────────────────────────────────┬───────────────────────────────────────┘
                                          │ all 5 events
                                          ▼
                             ┌────────────────────────┐
                             │        notifier        │
                             │   (simulated emails)   │
                             └────────────────────────┘
```

Arrows into the exchange are events a service publishes, arrows out are events it consumes — see
the event catalog below for exactly which.

### Components

| Component          | Tech                   | Port | Data store            | Responsibility                                                                          |
|--------------------|------------------------|------|-----------------------|------------------------------------------------------------------------------------------|
| `employee-service` | FastAPI                | 8001 | Postgres `employees_db` | Registration/login (issues JWTs), who reports to whom, submitting claims, claim status |
| `approval-service` | FastAPI                | 8002 | Redis                 | Manager approval inbox, approve/reject decisions                                        |
| `payment-service`  | FastAPI                | 8003 | Postgres `payments_db` | Simulates reimbursing approved claims, tracks payments, retries failed ones            |
| `notifier`         | Plain Python (no HTTP) | —    | —                     | Consumes every event and simulates emailing the employee (logs the email)              |

### Why event-driven?

- **Approving shouldn't wait on the bank.** When a manager approves, approval-service publishes
  one `expense.approved` event and returns immediately. It doesn't call payment-service directly —
  it doesn't even know payment-service exists. If payment-service is down, approvals queue up in
  RabbitMQ and get paid when it comes back; managers can keep approving.
- **One event, many reactions.** `expense.approved` is consumed by payment-service (pay it),
  employee-service (update the claim status), and notifier (email the employee). Adding a fourth
  reaction later (an audit log, an accounting export, …) means adding a consumer, not changing
  approval-service.
- **Events carry what consumers need.** Every event includes the employee's name, email, and the
  amount, so no consumer has to call back to another service to find them.

### Why does approval-service verify the JWT itself?

employee-service signs each JWT with `JWT_SECRET` and puts the employee's id, role, and name in it.
approval-service verifies the signature with the **same** secret and trusts what's inside — no HTTP
call to employee-service on every request. That's fast and keeps approvals working even if
employee-service is down, but it means both services must be configured with an identical
`JWT_SECRET` (a mismatch shows up as every request getting `401 Invalid or expired token`), and a
role change only takes effect when the employee logs in again.

### Event catalog (`expenses_exchange`, topic exchange)

| Routing key         | Published by     | Consumed by                                         | Payload                                                                                                         |
|---------------------|------------------|-----------------------------------------------------|------------------------------------------------------------------------------------------------------------------|
| `expense.submitted` | employee-service | approval-service, notifier                          | `{claim_id, employee_id, employee_email, employee_name, manager_id, amount, currency, category, description, submitted_at}` |
| `expense.approved`  | approval-service | payment-service, employee-service, notifier         | `{claim_id, employee_id, employee_email, employee_name, amount, currency, approved_by, decided_at}`              |
| `expense.rejected`  | approval-service | employee-service, notifier                          | `{claim_id, employee_id, employee_email, employee_name, amount, currency, rejected_by, reason, decided_at}`       |
| `payment.completed` | payment-service  | employee-service, notifier                          | `{claim_id, payment_id, employee_id, employee_email, employee_name, amount, currency, reference, paid_at}`       |
| `payment.failed`    | payment-service  | employee-service, notifier                          | `{claim_id, payment_id, employee_id, employee_email, employee_name, amount, currency, reason, attempts}`         |

### Claim lifecycle (as seen in employee-service)

```
SUBMITTED ──expense.approved──► APPROVED ──payment.completed──► PAID
    │                              │                              ▲
    │                              └──payment.failed──► PAYMENT_FAILED ──(retry succeeds)──┘
    └──expense.rejected──► REJECTED
```

Each event handler only moves a claim from a state it's allowed to come from, so a duplicate or
out-of-order message is ignored rather than corrupting the status. payment-service has a unique
constraint on `claim_id` for the same reason — RabbitMQ delivers at-least-once, and paying someone
twice is the worst bug this system could have.

### Payment simulation (`payment-service`, configurable via env)

| Setting                | Default | Effect                                                                   |
|------------------------|---------|---------------------------------------------------------------------------|
| `PAYMENT_SECONDS`      | `2`     | How long the simulated bank transfer takes                               |
| `PAYMENT_FAILURE_RATE` | `0.1`   | Share of payments that randomly fail with "bank transfer timed out"      |
| `PAYMENT_LIMIT`        | `5000`  | Claims above this always fail — a deterministic way to see the failure path |

A `FAILED` payment can be retried with `POST /payments/{claim_id}/retry`.

### Request flow: submit → approve → pay → notify

1. Register a `MANAGER`, and an `EMPLOYEE` whose `manager_id` points at them
   (`POST /auth/register` on employee-service). Both log in (`POST /auth/login`) to get a JWT.
2. The employee calls `POST /claims` on employee-service with their JWT. It refuses if they have no
   manager, saves the claim as `SUBMITTED` (with a snapshot of their `manager_id`), and publishes
   `expense.submitted`. notifier emails "We received your expense claim".
3. approval-service consumes `expense.submitted` and puts the claim in the manager's inbox in Redis.
4. The manager calls `GET /approvals/inbox` on approval-service with **their** JWT, then
   `POST /approvals/{claim_id}/approve` (or `/reject` with a `reason`). Only the employee's own
   manager can see or decide on the claim (`404` otherwise), only once (`409` after that), and only
   `MANAGER`s can use approval-service at all (`403`).
5. approval-service publishes `expense.approved` (or `expense.rejected`). employee-service updates
   the claim, notifier emails the employee.
6. payment-service consumes `expense.approved`, simulates the transfer, and publishes
   `payment.completed` (with a `TRX-…` reference) or `payment.failed`. employee-service marks the
   claim `PAID` or `PAYMENT_FAILED`, and notifier emails the result.

## Running locally

Each component is a standalone app configured entirely through environment variables (see each
service's `.env.example`). Since containers aren't in the picture yet, you need local Postgres, Redis,
and RabbitMQ instances reachable at the URLs in those files.

Quickest way to get all three running without installing anything system-wide (this is a stopgap
until the app itself is containerized):

```bash
docker run -d --name pg -e POSTGRES_PASSWORD=postgres -p 5432:5432 postgres:16
docker run -d --name redis -p 6379:6379 redis:7
docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management
```

Then create the two databases:

```bash
docker exec -it pg psql -U postgres -c "CREATE DATABASE employees_db;"
docker exec -it pg psql -U postgres -c "CREATE DATABASE payments_db;"
```

For each service, copy `.env.example` to `.env`, install dependencies, and run it:

```bash
cd services/employee-service
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload --port 8001
```

Repeat for `approval-service` (port 8002) and `payment-service` (port 8003). Tables are created
automatically on startup (`Base.metadata.create_all`) — no migrations tooling yet.

The notifier has no HTTP server — it just runs, and its "emails" show up in its logs:

```bash
cd services/notifier
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m app.main
```

### Try it end to end

```bash
# a manager, and an employee reporting to them
curl -X POST localhost:8001/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"mona@corp.com","password":"pw123456","full_name":"Mona","role":"MANAGER"}'
curl -X POST localhost:8001/auth/register -H 'Content-Type: application/json' \
  -d '{"email":"eman@corp.com","password":"pw123456","full_name":"Eman","manager_id":"<manager-id>"}'

# log both in and keep the tokens
EMP_TOKEN=$(curl -s -X POST localhost:8001/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"eman@corp.com","password":"pw123456"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')
MGR_TOKEN=$(curl -s -X POST localhost:8001/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"mona@corp.com","password":"pw123456"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["access_token"])')

# the employee submits a claim
curl -X POST localhost:8001/claims -H 'Content-Type: application/json' -H "Authorization: Bearer $EMP_TOKEN" \
  -d '{"amount":42.50,"category":"MEALS","description":"Client lunch","expense_date":"<today, YYYY-MM-DD>"}'

# the manager sees it in their inbox and approves it
curl localhost:8002/approvals/inbox -H "Authorization: Bearer $MGR_TOKEN"
curl -X POST localhost:8002/approvals/<claim-id>/approve -H "Authorization: Bearer $MGR_TOKEN"

# a couple of seconds later the claim is PAID, with a payment reference
curl localhost:8001/claims/<claim-id> -H "Authorization: Bearer $EMP_TOKEN"
curl localhost:8003/payments/<claim-id>
```

This has been run end to end and confirmed working: an approved claim goes `SUBMITTED` →
`APPROVED` → `PAID` with a `TRX-…` reference, a rejected claim ends up `REJECTED` with the manager's
reason, a 9000 claim ends up `PAYMENT_FAILED` (above the payout limit) and becomes `PAID` after a
retry with a higher limit, and notifier logs one email per step. With payment-service stopped,
approvals wait in the `payment_service.expense_approved` queue and get paid on restart. With a
different `JWT_SECRET` in approval-service, every request is rejected with `401`.

You can also:

- Watch the messages flow through `expenses_exchange` in the RabbitMQ management UI at
  `http://localhost:15672` (login `guest` / `guest`)
- See approval-service's state in Redis: `docker exec -it redis redis-cli KEYS '*'`
  (`approval:<claim_id>` per claim, `inbox:<manager_id>` per manager)
- Browse each API's interactive docs at `http://localhost:800{1,2,3}/docs`

## Follow along on YouTube

This repo is the demo project for the DevOps with David videos:

| Video | What you do with FlowApprove |
|-------|------------------------------|
| Linux Fundamentals, Part 1: Foundations | Explore the repo from the terminal: `find`, `grep`, pipes, permissions |
| Linux Fundamentals, Part 2: Linux in practice | Processes, services, env vars, networking, SSH, Bash scripting & `cron` |
| Git Fundamentals | Branches, merges & conflicts, undoing mistakes, PRs & code review |

Links will be added here as the videos go live.

For the Linux videos, use the free Ubuntu lab in [`lab/`](lab/): a container with systemd, so
services, logs, cron and timers work like on a real server.
