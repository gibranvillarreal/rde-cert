# Expected Outputs — Sample Scenarios

Defines what "good output" looks like for each sample input.
Use this to manually verify the pipeline is working correctly.

---

## Sample 1 — meeting1.txt (Sprint Planning)

**Command:**
```bash
python main.py --notes samples/meeting1.txt --backlog samples/backlog.json --verbose
```

**What the pipeline should detect:**

| Requirement from notes | Expected result |
|---|---|
| Comment threads on tasks | NEW story generated |
| File attachments on tasks | NEW story generated |
| Sprint and milestone planning view | NEW story generated |
| In-app notifications (bell icon) | NEW story generated |
| Export to PDF (mentioned) | DUPLICATE — matches PROJ-005 |

**Good output criteria:**
- At least 4 stories generated
- At least 1 duplicate detected (export to PDF)
- Each story has 2+ acceptance criteria
- Comment thread story should mention threading/parent-child, not just "add comments"
- File attachment story should mention file size limit (10MB was discussed)
- In-app notification story should be distinct from the email notification ticket

**Red flags (bad output):**
- Export to PDF generates a new story instead of being flagged as duplicate
- Acceptance criteria are vague (e.g. "feature works correctly")
- Stories are too large and should be split further

---

## Sample 2 — meeting2.txt (Client Requirements)

**Command:**
```bash
python main.py --notes samples/meeting2.txt --backlog samples/backlog.json --verbose
```

**What the pipeline should detect:**

| Requirement from notes | Expected result |
|---|---|
| Time tracking with timers | NEW story generated |
| Recurring tasks | NEW story generated |
| Client portal (read-only) | NEW story generated |
| Invoicing / QuickBooks integration | NEW story generated (or flagged as future/research) |
| Search (mentioned by Tom) | DUPLICATE — matches PROJ-006 |
| User profile (roles visible) | DUPLICATE — matches PROJ-007 |
| Audit log | NEW story generated |

**Good output criteria:**
- At least 4-5 stories generated
- At least 2 duplicates detected (search, user profile)
- Time tracking story should mention per-task, per-project, per-member views
- Client portal story should explicitly call out read-only access and separate login
- Recurring tasks story should mention configurable interval options
- Billing/QuickBooks may be categorized as "research" — acceptable given it was
  flagged as future scope in the meeting

**Red flags (bad output):**
- Search and user profile not flagged as duplicates
- Client portal story doesn't mention the read-only constraint
- Audit log missing from output entirely

---

## Sample 3 — meeting3.txt / meeting3.pdf (Security & Integration)

**Command (text version):**
```bash
python main.py --notes samples/meeting3.txt --backlog samples/backlog.json --verbose
```

**Command (PDF version — run generate_pdf.py first):**
```bash
python samples/generate_pdf.py
python main.py --notes samples/meeting3.pdf --backlog samples/backlog.json --verbose
```

**What the pipeline should detect:**

| Requirement from notes | Expected result |
|---|---|
| Two-factor authentication (2FA) | NEW story generated |
| Audit log | NEW story generated |
| API access with token auth | NEW story generated |
| Webhooks for real-time events | NEW story (or combined with API story) |
| Single Sign-On (SSO / SAML) | NEW story generated |

**Good output criteria:**
- 4-5 stories generated (API and webhooks may be combined or split)
- 2FA story mentions TOTP standard and admin enforceability
- SSO story mentions SAML 2.0 / OAuth2 and identity providers
- Audit log story mentions 90-day retention and CSV export (from the document)
- PDF version produces the same stories as the txt version

**Red flags (bad output):**
- Webhook and API treated as same requirement and only one story generated
- 2FA story is generic ("add two-factor auth") without specifics from the doc
- PDF parse fails or produces garbled text

---

## Cross-sample expectations (applies to all)

- All stories have `priority`, `category`, and `estimated_complexity` set
- No story has `as_a: "user"` — must be a specific role
- Acceptance criteria are testable statements, not descriptions
- The self-critique step should catch any vague stories and refine them
- Summary paragraph accurately describes what was found
