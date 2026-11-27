# Ticket Support System

## 1. Overview

The purpose of this application is to provide a customer support system through a feature called **Ticket**.

Regular users can create support tickets to request assistance. Users with `is_staff=True` are considered support staff and are responsible for handling and responding to tickets.

The system consists of two main models:

- **Ticket:** Stores support request information and ticket-related attachments.
- **TicketMessage:** Stores messages, replies, and message-related attachments.

---

## 2. User Model Reference

The application uses Django's built-in User model.

### User Model

Use:

`settings.AUTH_USER_MODEL`

All user-related ForeignKey relationships must reference `settings.AUTH_USER_MODEL`.

Do not directly import or reference the User class.

### User Roles

User roles are determined using Django's built-in `is_staff` attribute:

- `is_staff=True`: Support Staff.
- `is_staff=False`: Regular User.

Do not create a separate support staff model or a custom User model.

---

## 3. Database Models

### 3.1. Ticket Model

The `Ticket` model represents an individual support request.

| Field | Type / Reference | Description |
|---|---|---|
| id | PrimaryKey | Unique ticket identifier |
| user | ForeignKey(AUTH_USER_MODEL) | Ticket owner |
| subject | CharField | Ticket subject |
| category | Field | Ticket category |
| priority | Field | Ticket priority |
| status | Field | Current ticket status |
| created_at | DateTimeField | Ticket creation timestamp |
| updated_at | DateTimeField | Last update timestamp |
| expire_at | DateTimeField | Ticket expiration timestamp |
| file | FileField | Optional ticket attachment |

### 3.2. TicketMessage Model

The `TicketMessage` model stores messages and replies exchanged within a ticket.

| Field | Type / Reference | Description |
|---|---|---|
| id | PrimaryKey | Unique message identifier |
| ticket | ForeignKey(Ticket) | Related ticket |
| sender | ForeignKey(AUTH_USER_MODEL) | Message sender |
| body | TextField | Message content |
| created_at | DateTimeField | Message creation timestamp |
| file | FileField | Optional message attachment |

### Relationships

- Each Ticket belongs to exactly one User.
- Each Ticket can have multiple TicketMessages.
- Each TicketMessage belongs to exactly one Ticket.
- Each TicketMessage has one sender.
- Both `Ticket.user` and `TicketMessage.sender` reference `settings.AUTH_USER_MODEL`.
- Both Ticket and TicketMessage can optionally contain an uploaded file.

---

## 4. User Roles & Permissions

### 4.1. Regular Users

Regular users have the following permissions:

- Create new tickets.
- View only their own tickets.
- View messages belonging to their own tickets.
- Reply to support staff messages within their own tickets.
- Update their own tickets.
- Upload files to their own tickets.
- Upload files when sending ticket messages.

Regular users must NOT be able to:

- View tickets created by other users.
- View messages belonging to other users' tickets.
- Reply to tickets they do not own.
- Modify ticket priority or status.
- Change ticket expiration dates.
- Close tickets.

Regular users can only view the following Ticket fields:

- `subject`
- `category`
- `status`

Other Ticket fields must remain hidden from regular users.

### 4.2. Support Staff

A user with `is_staff=True` is considered a support staff member.

Support staff have the following permissions:

- View and manage all support tickets.
- Respond to any ticket.
- Continue existing conversations.
- Set and modify ticket priority.
- Set and modify ticket status.
- Increase or decrease ticket expiration dates.
- Close tickets.
- View ticket messages and conversation history.
- Access ticket attachments and message attachments.

Only support staff can manage ticket priority, status, expiration dates, and ticket closure.

---

## 5. Ticket Lifecycle

- When a ticket is created, its creation timestamp must be stored in `created_at`.
- The default expiration period is one month after ticket creation.
- Only support staff can increase or decrease the expiration date.
- Regular users cannot modify `expire_at`.
- When a ticket reaches its expiration date, it must be automatically closed.
- Whenever a ticket is updated, its `updated_at` timestamp must be updated.
- Only support staff can manually close a ticket.

Ticket expiration must be handled automatically, even when no user visits the ticket.

---

## 6. Ticket Message Rules

- Support staff can send messages to any ticket.
- Regular users can reply within their own tickets.
- Regular users cannot send messages to tickets owned by other users.
- Every message must be associated with a specific ticket.
- The sender must be recorded for every message.
- Only the ticket owner and support staff can read ticket messages.
- Messages must not be modified by unauthorized users.

---

## 7. File Upload Management

The system supports two types of file attachments.

### 7.1. Ticket Attachments

The `Ticket.file` field stores files attached directly to a support ticket.

- Regular users can upload files to their own tickets.
- Support staff can access ticket attachments.
- Ticket attachments must follow ticket ownership permissions.

### 7.2. Ticket Message Attachments

The `TicketMessage.file` field stores files attached to individual messages.

- Both regular users and support staff can upload message attachments.
- Each attachment must be associated with its corresponding message.
- Attachments must follow the same access permissions as their parent ticket.
### 7.3. File Upload Security

File uploads are considered private and sensitive resources.

The following security rules are mandatory:

**Storage Security**
- Never store ticket attachments in publicly accessible directories.
- Store uploaded files in private storage.
- Do not expose direct public URLs to uploaded files.
- Generate unique filenames instead of trusting user-provided filenames.
- Prevent executable files from being uploaded or executed.
- Never allow uploaded files to overwrite existing files.

**File Validation**
- Validate file extensions.
- Validate MIME types and actual file content.
- Do not trust the Content-Type header provided by the client.
- Enforce maximum file size limits.
- Restrict allowed file types to a predefined whitelist.
- Reject suspicious or potentially dangerous files.
- Consider malware scanning for uploaded files.

**Access Control**
- Every file download must pass through an authenticated backend endpoint.
- Before serving a file, verify that the requesting user is either:
  - The owner of the associated ticket.
  - A support staff member (`is_staff=True`).
- Regular users must never access attachments belonging to other users' tickets.
- Apply the same authorization rules to both Ticket and TicketMessage attachments.
- Never rely on unguessable file URLs as an authorization mechanism.

**Download Security**
- Do not expose physical storage paths.
- Prevent directory traversal attacks.
- Use safe Content-Disposition headers when serving files.
- Never serve potentially executable uploads as executable content.
- Use appropriate response headers to reduce browser-based security risks.

**Implementation Requirements**
- File authorization must be enforced on the server side.
- File validation must happen before saving uploads.
- File access must be checked on every download request.
- Deleting a ticket or attachment must follow the project's file lifecycle and retention rules.
- Do not bypass Django's authentication and authorization mechanisms.

These security requirements apply to both `Ticket.file` and `TicketMessage.file`.

### Security Requirements

- File uploads must be validated.
- Restrict allowed file types and file sizes.
- Do not expose uploaded files through publicly accessible URLs without authorization.
- Only the ticket owner and support staff can access ticket-related files.
- Prevent unauthorized file access and downloads.

---

## 8. Access Control Summary

| Action | Regular User | Support Staff |
|---|---|---|
| Create Ticket | Yes | Yes |
| View Own Tickets | Yes | Yes |
| View Other Users' Tickets | No | Yes |
| Read Ticket Messages | Own Tickets | All Tickets |
| Send Ticket Messages | Own Tickets | All Tickets |
| Update Own Ticket | Yes | Yes |
| Upload Ticket Files | Own Tickets | Yes |
| Upload Message Files | Own Tickets | All Tickets |
| Modify Priority | No | Yes |
| Modify Status | No | Yes |
| Modify Expiration Date | No | Yes |
| Close Ticket | No | Yes |

---

## 9. Important Implementation Rules

- All views must use Class-Based Views (CBVs).
- Use `settings.AUTH_USER_MODEL` for all user-related model relationships.
- All permissions must be checked on the backend.
- Querysets must be filtered according to user roles and ticket ownership.
- Never rely exclusively on frontend restrictions for access control.
- Ticket messages must always be validated against their associated ticket.
- File access must follow ticket ownership and support staff permissions.
- Expired tickets must be closed automatically.
- Follow the existing project architecture and coding standards.


## 10 api

- you can see all api in the docs/api.md