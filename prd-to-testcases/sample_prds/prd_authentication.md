# PRD: User Authentication — Login, Registration & Password Reset

**Author:** Identity Platform Team  
**Status:** Final  
**Version:** 2.0  
**Last Updated:** 2024-02-01

---

## Overview

This PRD covers the user authentication flows for PocketToons: account registration, login, and password recovery. Authentication is the critical entry point into the product and directly impacts conversion, retention, and security.

---

## Goals

- Provide a fast, frictionless login experience
- Reduce account-takeover incidents by enforcing modern security practices
- Support social login to reduce registration drop-off

---

## User Stories

1. **As a new user**, I want to create an account with my email and a password.
2. **As a returning user**, I want to log in quickly using my email/password or Google/Apple.
3. **As a user who forgot my password**, I want to reset it via a link sent to my email.
4. **As a user**, I want my session to persist across app restarts so I don't have to log in every time.
5. **As an admin**, I want to be able to lock accounts that show suspicious behaviour.

---

## Functional Requirements

### Registration

- **FR-1**: Users can register with an email address and password.
- **FR-2**: Email addresses must be validated (format check + uniqueness check).
- **FR-3**: Password must be at least 8 characters, contain one uppercase letter, one number, and one special character.
- **FR-4**: A verification email is sent upon registration. The account is inactive until verified.
- **FR-5**: The verification link expires after 24 hours. Users can request a new one.
- **FR-6**: Users can register via Google OAuth 2.0 or Sign in with Apple.

### Login

- **FR-7**: Users can log in with email + password.
- **FR-8**: After 5 consecutive failed login attempts, the account is locked for 15 minutes.
- **FR-9**: A CAPTCHA is shown after 3 consecutive failed attempts.
- **FR-10**: Login via Google OAuth or Apple Sign-In is supported.
- **FR-11**: A "Remember me" option persists the session for 30 days.
- **FR-12**: Login sessions expire after 7 days of inactivity without "Remember me".

### Password Reset

- **FR-13**: Users can request a password reset from the login screen.
- **FR-14**: A reset link is sent to the registered email within 60 seconds.
- **FR-15**: The reset link is single-use and expires after 1 hour.
- **FR-16**: Users must enter and confirm the new password on the reset page.
- **FR-17**: After a successful reset, all existing sessions for that account are invalidated.
- **FR-18**: Users cannot reuse their last 3 passwords.

### Session Management

- **FR-19**: JWT tokens are used for session management.
- **FR-20**: Refresh tokens are rotated on each use.
- **FR-21**: Users can view active sessions and revoke any session from Account Settings.

### Account Security

- **FR-22**: Accounts can be locked by admins. Locked accounts see a specific error message.
- **FR-23**: Successful and failed login attempts are logged with IP address and timestamp.

---

## Non-Functional Requirements

- **NFR-1**: Login API must respond within 500ms at P99.
- **NFR-2**: Passwords must be hashed using bcrypt with a minimum cost factor of 12.
- **NFR-3**: All authentication endpoints must be HTTPS only.
- **NFR-4**: The system must handle 10,000 concurrent login requests without degradation.

---

## Edge Cases & Constraints

- Users who register via Google and later try to log in with email/password should see a helpful message directing them to use Google login.
- If a user's email changes (future feature), all sessions must be invalidated.
- Deleted accounts must not be re-registerable with the same email for 30 days.
- OAuth failures (Google/Apple service down) must degrade gracefully with a fallback message.
