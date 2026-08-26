# Email Automation - Modular Architecture

## Overview

The email automation project has been refactored into modular, focused components for better maintainability, testability, and extensibility.

## Module Structure

```
email_automation/
├── email_automation.py      # Main entry point (orchestrates CLI)
├── config.py                # Configuration & environment setup
├── db.py                    # SQLAlchemy engine/session setup
├── models.py                # SQLAlchemy ORM models (Email, CandidateResponse)
├── state_manager.py         # Candidate state persistence (PostgreSQL)
├── token_manager.py         # Tracking token generation & extraction
├── gmail_client.py          # Gmail SMTP/IMAP connections
├── email_handler.py         # Email building & parsing
├── sender.py                # Invitation sending logic
├── reply_classifier.py      # Reply classification (interested/declined/review)
├── llm_reply_classifier.py  # Ollama LLM fallback for ambiguous replies
├── monitor.py               # Reply monitoring loop
├── cli.py                   # Command-line interface
├── db/                      # Dockerfile + docker-compose.yml for postgres-db
└── .env                     # Environment variables (required)
```

## Module Descriptions

### `config.py`
**Purpose**: Centralized configuration management

- Loads environment variables (`.env` file)
- Defines constants (SMTP/IMAP servers, timeouts, polling intervals)
- Validates required configuration via `require_config()`

**Key Constants**:
- `GMAIL_ADDRESS`, `GMAIL_APP_PASSWORD`
- `POLL_INTERVAL_SECONDS`, `MAX_MONITOR_MINUTES`
- `GMAIL_SMTP_SERVER`, `GMAIL_IMAP_SERVER`

---

### `state_manager.py`
**Purpose**: Manages candidate state persistence

- Backed by PostgreSQL (`emails` / `candidate_responses` tables) via `db.py` + `models.py`
- Reply tracking still keys off the token embedded in the email subject

**Key Functions**:
- `save_sent_email(token, candidate_email, candidate_name, subject, body, sent_at)` - Record a sent invitation
- `get_pending_tokens()` - Tokens with no reply yet
- `get_candidate_email(token)` - Expected sender for a token
- `record_reply(token, subject, body, received_at)` - Store an incoming reply
- `get_reply_body(token)` - Most recent unclassified reply body for a token
- `set_classification(token, classification, analyzed_at)` - Store the classification result

**Storage**: PostgreSQL, `emails` and `candidate_responses` tables (see `db/Dockerfile` and `db/docker-compose.yml` for the local Postgres container). `DATABASE_URL` in `.env` points at it.

---

### `token_manager.py`
**Purpose**: Handles tracking token generation and extraction

- Generates unique 8-character UUIDs for each invitation
- Extracts tokens from email subjects using regex

**Key Functions**:
- `generate_token()` - Creates unique tracking ID
- `extract_token(subject)` - Parses `[Ref:xxxxxxxx]` from subject

**Token Format**: `[Ref:abc12345]` in email subject

---

### `gmail_client.py`
**Purpose**: Wrapper for Gmail SMTP/IMAP operations

- Handles SMTP connection and email sending
- Manages IMAP inbox connection
- Provides clean connection/disconnection

**Key Functions**:
- `send_message(message)` - Send email via SMTP
- `connect_to_inbox()` - Connect to Gmail IMAP
- `disconnect_inbox(mail)` - Safely close IMAP connection

**Error Handling**: Graceful failures with logging

---

### `email_handler.py`
**Purpose**: Email composition and parsing

- Builds invitation email messages
- Extracts plain text from received emails
- Handles multipart emails and attachments

**Key Functions**:
- `build_invite_message()` - Create EmailMessage for sending
- `get_email_body()` - Extract text content from received email
- `parse_email_bytes()` - Convert raw email to structured data

---

### `sender.py`
**Purpose**: End-to-end invitation sending

- Orchestrates: token generation → email building → SMTP sending → state save
- Single public function: `send_invite()`

**Flow**:
1. Generate unique token
2. Build email with token in subject
3. Send via Gmail SMTP
4. Create state record
5. Persist to JSON

---

### `reply_classifier.py`
**Purpose**: Classify candidate replies

- Rule-based keyword matching for the obvious cases
- Ambiguous replies fall through to `llm_reply_classifier.py` before
  defaulting to manual review

**Classification Results**:
- `"interested"` - Keywords "interested"/"yes", or LLM label `INTERESTED`
- `"declined"` - Keywords "not interested"/"decline", or LLM label `NOT_INTERESTED`
- `"needs_review"` - LLM label `OTHER`, or if the LLM is unreachable

---

### `llm_reply_classifier.py`
**Purpose**: LLM fallback for replies the rule-based pass can't categorize

- Calls an OSS model through Ollama (via `langchain-ollama`) per the
  Module 3 PDD's intent-analysis step
- Returns one of `INTERESTED`, `NOT_INTERESTED`, `OTHER`
- Raises on failure (unreachable server, missing model) so the caller
  can decide the fallback - `reply_classifier.py` catches this and
  defaults to `needs_review`

**Key Function**:
- `classify_reply_llm(body)` - Classify reply text via Ollama

**Config** (`config.py`, both optional with defaults):
- `OLLAMA_MODEL` (default `gpt-oss:120b-cloud`)
- `OLLAMA_BASE_URL` (default `http://localhost:11434`)

---

### `monitor.py`
**Purpose**: Main polling loop for reply monitoring

- Continuously checks IMAP for unseen emails
- Matches replies to candidates via token
- Classifies replies
- Persists updates

**Flow**:
1. Connect to IMAP
2. Search for UNSEEN emails
3. For each email:
   - Extract token from subject
   - Verify sender matches candidate
   - Get email body
   - Update state
4. Classify new replies
5. Sleep, repeat until all replied or timeout

---

### `cli.py`
**Purpose**: Command-line interface

- Argument parsing
- Command routing (send/monitor)
- Result logging

**Commands**:
- `python email_automation.py send --to email1@example.com [email2@example.com ...] [--name "Name"]`
- `python email_automation.py monitor`

---

### `email_automation.py`
**Purpose**: Main entry point

- Sets up logging
- Imports and calls `cli.main()`
- Handles top-level exceptions

---

## Usage Examples

### Send single invitation
```bash
python email_automation.py send --to candidate@example.com
```

### Send to multiple candidates with same name
```bash
python email_automation.py send --to person1@example.com person2@example.com --name "Jane Doe"
```

### Monitor inbox for replies
```bash
python email_automation.py monitor
```

---

## Dependency Graph

```
email_automation.py (entry point)
    ↓
cli.py (argument parsing)
    ├→ sender.py (send command)
    │   ├→ config.py
    │   ├→ state_manager.py → db.py, models.py (PostgreSQL)
    │   ├→ token_manager.py
    │   ├→ email_handler.py
    │   └→ gmail_client.py
    │
    └→ monitor.py (monitor command)
        ├→ config.py
        ├→ state_manager.py → db.py, models.py (PostgreSQL)
        ├→ gmail_client.py
        ├→ token_manager.py
        ├→ email_handler.py
        └→ reply_classifier.py
            └→ llm_reply_classifier.py (ambiguous replies only)
```

---

## Benefits of Modular Architecture

### Maintainability
- Each module has a single, clear responsibility
- Easier to locate and fix bugs
- Changes isolated to relevant modules

### Testability
- Each module can be unit tested independently
- Mock dependencies easily
- Test fixtures for state, emails, tokens

### Extensibility
- Replace `reply_classifier.py` with ML model
- Swap email backend (e.g., SendGrid, Mailgun)
- Add webhooks, API endpoints, etc.

### Reusability
- Import individual modules in other scripts
- Use `sender.send_invite()` programmatically
- Build web dashboard using monitor logic

---

## Extension Examples

### 1. Add Email Template System
Extend `email_handler.py` with template engine for dynamic content.

### 2. Build REST API
Use `sender.py` and `monitor.py` as backend for Flask/FastAPI endpoints.

### 3. Add Email Scheduling
Modify `sender.py` to accept scheduled send times, persist with state.

---

## Testing Strategy

### Unit Tests per Module
```python
# test_token_manager.py
def test_generate_token():
    token = generate_token()
    assert len(token) == 8
    
def test_extract_token():
    subject = "Re: Interview Invitation [Ref:abc12345]"
    token = extract_token(subject)
    assert token == "abc12345"

# test_reply_classifier.py
def test_classify_interested():
    body = "Yes, I'm very interested!"
    assert classify_reply(body) == "interested"
```

### Integration Tests
- Mock Gmail IMAP/SMTP
- Test send → monitor flow
- Verify state transitions

---

## Configuration (.env)

Required environment variables:
```
GMAIL_ADDRESS=your-email@gmail.com
GMAIL_APP_PASSWORD=your-app-specific-password
DATABASE_URL=postgresql+psycopg2://postgres:postgres@localhost:5432/hr_automation
```

**Note**: Use Gmail App Passwords, not your main password. `DATABASE_URL` must point at a running Postgres instance - see `db/docker-compose.yml`.

---

## Logging

All modules log to both:
- `recruiting_mailer.log` - File output
- Console (`stdout`) - Terminal output

Log levels:
- `INFO` - General operations (send, monitor start/end)
- `DEBUG` - Detailed operations (state save, IMAP operations)
- `WARNING` - Non-fatal issues (sender mismatch, search failures)
- `ERROR` - Fatal issues (SMTP failure, missing config)

---

## Future Improvements

1. **Database**: Replace JSON with PostgreSQL/SQLite
2. **ML Classifier**: Ollama fallback is in (`llm_reply_classifier.py`) - consider using it as the primary classifier instead of a fallback
3. **Email Templates**: Support custom HTML templates
4. **Scheduling**: Queue emails for later sending
5. **Webhooks**: Notify external systems on reply
6. **Web UI**: Dashboard to manage candidates and view replies
7. **Batch Processing**: Process multiple candidate CSVs
8. **Bounce Handling**: Track soft/hard bounces
