# Account & Group Endpoints

> Session-authenticated HTML/form endpoints (`POST` requests require a CSRF token).

## Auth (`/accounts/`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET`, `POST` | `/accounts/login/` | Public | Log in |
| `POST` | `/accounts/logout/` | Authenticated | Log out |
| `GET`, `POST` | `/accounts/password_change/` | Authenticated | Change password |
| `GET`, `POST` | `/accounts/password_reset/` | Public | Request password reset email |
| `GET`, `POST` | `/accounts/reset/<uidb64>/<token>/` | Public (valid token) | Set new password |

## Profile (`/account/`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/account/` | Optional | Home / dashboard |
| `GET`, `POST` | `/account/signup/` | Unauthenticated | Register user (`role="none"` assigned automatically) |
| `GET` | `/account/profile/` | Authenticated | View own profile |
| `GET`, `POST` | `/account/profile/edit/` | Authenticated (Owner) | Edit `first_name`, `last_name`, `email`, `bio`, `profile_picture` (max 2MB) |
| `POST` | `/account/profile/picture/delete/` | Authenticated (Owner) | Remove profile picture |
| `GET` | `/account/profile/<int:user_id>/` | Self or Same Group | View teammate profile (enforces group isolation) |

## WorkGroup & Roles (`/account/group/`)

| Method | Endpoint | Access | Description |
|---|---|---|---|
| `GET` | `/account/group/` | Group Member | View own group & members |
| `GET`, `POST` | `/account/group/create/` | User without Group | Create group & set owner role to `manager` |
| `GET`, `POST` | `/account/group/edit/` | Group Manager | Update group `name` & `description` |
| `GET`, `POST` | `/account/group/delete/` | Group Manager | Delete group & reset members to `none` |
| `POST` | `/account/group/members/add/` | Group Manager | Add ungrouped user (`username`) as `member` |
| `POST` | `/account/group/members/<int:user_id>/remove/` | Group Manager | Remove member & reset role to `none` |
| `POST` | `/account/group/members/<int:user_id>/transfer/` | Group Manager | Transfer ownership (`manager` <-> `member`) |
| `POST` | `/account/group/leave/` | Non-owner Member | Leave group & reset role to `none` |





# Support Ticket API

All endpoints require an authenticated session (`401 Unauthorized` if unauthenticated).

## User Endpoints

- `POST /api/support/tickets/` — Create a new support ticket (`subject`, `category`, optional `file`).
- `GET /api/support/tickets/` — List tickets owned by the authenticated user (returns `id`, `subject`, `category`, `status` for regular users).
- `GET /api/support/tickets/{id}/` — Retrieve ticket details (enforces ownership or staff authorization).
- `POST /api/support/tickets/{id}/messages/` — Post a reply message (`body`, optional `file`) to an open ticket.
- `GET /api/support/tickets/{id}/messages/` — Retrieve conversation history for an authorized ticket.

## Support Staff Endpoints (`is_staff=True`)

- `PATCH /api/support/tickets/{id}/close/` — Close a ticket.
- `GET /api/support/staff/tickets/` — List all support tickets with full metadata (`priority`, `expire_at`, `assigned_to`, timestamps).
- `PATCH /api/support/staff/tickets/{id}/` — Update ticket `priority`, `status`, or `expire_at` (ISO-8601 datetime).
- `POST /api/support/staff/tickets/{id}/assign/` — Assign ticket to a support staff user (`staff_user_id`, defaults to current staff user).