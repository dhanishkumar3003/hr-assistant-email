# Email Automation - Modular Architecture

## Overview

The email automation project has been refactored into modular, focused components for better maintainability, testability, and extensibility.

## Module Structure

```
email_automation/
├── emailautomation.py       # Main entry point (orchestrates CLI)
├── config.py                # Configuration & environment setup
├── state_manager.py         # Candidate state persistence (JSON)
├── token_manager.py         # Tracking token generation & extraction
├── gmail_client.py          # Gmail SMTP/IMAP connections
├── email_handler.py         # Email building & parsing
├── sender.py                # Invitation sending logic
├── reply_classifier.py      # Reply classification (interested/declined/review)
├── monitor.py               # Reply monitoring loop
├── cli.py                   # Command-line interface
├── candidates_state.json    # Persistent state file (auto-created)
├── recruiting_mailer.log    # Log file (auto-created)
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

- Loads/saves candidate state from JSON file
- Creates structured candidate records
- Filters pending candidates

**Key Functions**:
- `load_state()` - Load from disk
- `save_state(state)` - Persist to disk
- `get_pending_tokens(state)` - Get "sent" status candidates
- `create_candidate_record()` - Build new record structure

**State Record Structure**:
```json
{
  "token": {
    "candidate_email": "person@example.com",
    "candidate_name": "Jane Doe",
    "sent_at": "2024-01-15T10:30:00+00:00",
    "status": "sent|replied|classified",
    "reply_body": "Yes, I'm interested!",
    "classification": "interested|declined|needs_review",
    "replied_at": "2024-01-15T11:45:00+00:00"
  }
}
```

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

- Rule-based classifier (can be replaced with ML/LLM)
- Detects interest, decline, or ambiguity

**Classification Results**:
- `"interested"` - Keywords: "interested", "yes"
- `"declined"` - Keywords: "not interested", "decline"
- `"needs_review"` - Default (ambiguous)

**Future**: Can integrate Ollama or other ML models

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
- `python emailautomation.py send --to email1@example.com [email2@example.com ...] [--name "Name"]`
- `python emailautomation.py monitor`

---

### `emailautomation.py`
**Purpose**: Main entry point

- Sets up logging
- Imports and calls `cli.main()`
- Handles top-level exceptions

---

## Usage Examples

### Send single invitation
```bash
python emailautomation.py send --to candidate@example.com
```

### Send to multiple candidates with same name
```bash
python emailautomation.py send --to person1@example.com person2@example.com --name "Jane Doe"
```

### Monitor inbox for replies
```bash
python emailautomation.py monitor
```

---

## Dependency Graph

```
emailautomation.py (entry point)
    ↓
cli.py (argument parsing)
    ├→ sender.py (send command)
    │   ├→ config.py
    │   ├→ state_manager.py
    │   ├→ token_manager.py
    │   ├→ email_handler.py
    │   └→ gmail_client.py
    │
    └→ monitor.py (monitor command)
        ├→ config.py
        ├→ state_manager.py
        ├→ gmail_client.py
        ├→ token_manager.py
        ├→ email_handler.py
        └→ reply_classifier.py
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
- Add new storage (e.g., database instead of JSON)
- Add webhooks, API endpoints, etc.

### Reusability
- Import individual modules in other scripts
- Use `sender.send_invite()` programmatically
- Build web dashboard using monitor logic

---

## Extension Examples

### 1. Add Database Storage
Replace `state_manager.py` with database operations while keeping the same interface.

### 2. Integrate ML Classifier
Replace simple rules in `reply_classifier.py` with Ollama or Claude API calls.

### 3. Add Email Template System
Extend `email_handler.py` with template engine for dynamic content.

### 4. Build REST API
Use `sender.py` and `monitor.py` as backend for Flask/FastAPI endpoints.

### 5. Add Email Scheduling
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
```

**Note**: Use Gmail App Passwords, not your main password.

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
2. **ML Classifier**: Integrate Claude/Ollama for smarter classification
3. **Email Templates**: Support custom HTML templates
4. **Scheduling**: Queue emails for later sending
5. **Webhooks**: Notify external systems on reply
6. **Web UI**: Dashboard to manage candidates and view replies
7. **Batch Processing**: Process multiple candidate CSVs
8. **Bounce Handling**: Track soft/hard bounces
