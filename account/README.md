# Account Management System

## 1. Overview

The purpose of this application is to manage user accounts, roles, and group-related access control within the project management platform.

The application is responsible for:

- Managing user roles.
- Managing user relationships with groups.
- Controlling access to group-related information.
- Enforcing role-based permissions.
- Ensuring data isolation between different groups.

The implementation must follow the existing application architecture and directory structure.

Do not redesign or restructure the application unnecessarily.

---

## 2. User Roles

The application uses a `role` field to determine each user's role and access level.

There are exactly four available roles:

| Role | Description |
|---|---|
| `none` | A regular user who does not belong to any group. |
| `admin` | A specially authorized platform-level user, such as the application developer or company CEO. |
| `member` | A user who belongs to a group. |
| `manager` | A user who owns or manages a group. |

Each user can have exactly one role at a time.

### 2.1. None

The `none` role is assigned to newly registered users by default.

A user with this role:

- Has an account in the application.
- Does not belong to any group.
- Does not have access to group-specific information.
- Can access their own account information.
- Can become a member or manager after joining or creating a group, according to the application's existing group management logic.

### 2.2. Member

The `member` role is assigned to users who belong to a group.

A member can:

- Access their own group's information according to the existing permissions.
- View members belonging to their own group.
- Participate in group-related activities according to their permissions.
- Access resources belonging to their own group when authorized.

A member must NOT be able to:

- View information belonging to other groups.
- View members of other groups.
- Access another group's resources.
- Modify their own role.
- Assign roles to other users.

### 2.3. Manager

The `manager` role is assigned to users who own or manage a group.

A manager can:

- Manage their own group according to the application's permissions.
- View members of their own group.
- Manage group-related operations.
- Access their group's information and resources.
- Perform management actions that are explicitly authorized by the application.

A manager must NOT automatically have access to other groups' private information.

A manager cannot assign themselves the `admin` role.

### 2.4. Admin

The `admin` role is reserved for specially authorized individuals, such as:

- The application developer.
- The company CEO.
- Other explicitly authorized platform administrators.

Admin privileges must be assigned through a trusted administrative process.

An ordinary user must never be able to assign the `admin` role to themselves or another user.

Admin permissions must be explicitly enforced through backend authorization.

Do not assume that the `admin` role automatically bypasses every group-level security restriction. Follow the project's existing administrative access policy.

---

## 3. Role Assignment & Management

Roles must be managed by the backend.

### Default Role

- Every newly registered user must receive the `none` role.
- Users must never be able to submit their own role during registration.
- The default role must be assigned automatically.

### Role Transitions

The expected role transitions are:

| Event | Resulting Role |
|---|---|
| User registers | `none` |
| User joins a group | `member` |
| User becomes a group's owner | `manager` |
| User is explicitly authorized as a platform administrator | `admin` |

Additional rules:

- Role changes must be handled by trusted backend logic.
- Regular users must never be able to modify their own role.
- Role changes must not be possible through manipulated POST requests.
- Role assignments must remain consistent with group ownership and membership relationships.
- When group membership or ownership changes, the corresponding role must be updated according to the application's business rules.

### Important Role Constraint

Each user has exactly one global role.

Before implementing role assignment, inspect the existing group membership and ownership models.

If the existing application allows a user to belong to multiple groups or own one group while belonging to another, a single global role may not fully represent all group-specific relationships.

Do not silently redesign the role system or introduce per-group roles. Preserve the existing architecture and report this conflict before making structural changes.

---

## 4. Group Data Isolation

Data isolation between groups is a fundamental security requirement.

Each group must have access only to its own information.

### Group Privacy Rules

- Groups must not have access to other groups' private information.
- Group members can only view members belonging to their own group.
- Members cannot retrieve information about members of other groups.
- Group resources must be isolated.
- Group-related queries must always respect group ownership and membership.
- Access to group data must be validated on the backend.

### Member Visibility

A regular member can:

- View their own profile.
- View other members belonging to their own group, subject to existing permissions.
- Access authorized group information.

A regular member cannot:

- View members of other groups.
- Access another group's member list.
- Retrieve another group's information by changing URL parameters or object IDs.
- Access another group's private resources.

### Manager Visibility

A manager can manage and view members of their own group.

A manager must not automatically gain access to another group's members or information.

---

## 5. Database Guidelines

The role functionality must be implemented within the existing account database architecture.

### Role Field

The application must support the following role values:

- `none`
- `admin`
- `member`
- `manager`

Requirements:

- Use Django model choices.
- Set `none` as the default value for new users.
- Validate role values.
- Prevent unauthorized role modifications.
- Keep role values consistent throughout the application.

### Database Rules

- Inspect existing models before making changes.
- Reuse existing user and group relationships.
- Do not introduce duplicate models.
- Do not create unnecessary database tables.
- Preserve existing database records.
- Use appropriate ForeignKey and relationship constraints.
- Use Django migrations for database schema changes.
- Never perform destructive database operations without explicit approval.

---

## 6. Authentication & Authorization

Authentication and authorization must be handled using the existing project authentication architecture.

### Authentication

- Use the existing authentication system.
- Identify the authenticated user through `request.user`.
- Never trust user IDs submitted by the client.
- Require authentication for protected account and group operations.

### Authorization

- Check user roles before performing restricted actions.
- Verify group membership before providing group-related information.
- Verify group ownership before allowing management operations.
- Never rely exclusively on frontend restrictions.
- Apply permission checks to every relevant request.
- Prevent IDOR (Insecure Direct Object Reference) vulnerabilities.
- Return appropriate HTTP responses when access is denied.

### Role Security

- Never trust role values received from the client.
- Never allow ordinary users to modify their own roles.
- Protect administrative role assignments.
- Role changes must only happen through authorized backend operations.

---

## 7. Django Development Standards

### Views

- Always use Class-Based Views (CBVs).
- Never use Function-Based Views (FBVs).
- Prefer Django Generic Class-Based Views when appropriate.
- Use Mixins when they provide a clear benefit.
- Follow existing view organization and naming conventions.
- Keep views focused on HTTP request and response handling.
- Avoid duplicating business logic across views.

### Models

- Follow existing model conventions.
- Keep model responsibilities clear.
- Use appropriate field types and constraints.
- Use meaningful relationship names.
- Avoid unnecessary abstractions.

### Forms

- Use Django Forms or ModelForms where appropriate.
- Validate all user-submitted data.
- Never rely exclusively on frontend validation.
- Do not expose restricted fields through forms.

---

## 8. Security Requirements

Security is a critical requirement of this application.

- Prevent privilege escalation.
- Prevent unauthorized role modifications.
- Prevent users from accessing other groups' information.
- Validate all incoming data.
- Protect against IDOR vulnerabilities.
- Enforce permissions on the backend.
- Use CSRF protection.
- Prevent SQL injection and XSS vulnerabilities.
- Never expose sensitive account information.
- Never trust user-provided group IDs or role values without authorization checks.

All group-related queries must be appropriately scoped to the authenticated user's authorized groups.

---

## 9. Testing Guidelines

Write tests for all important role and permission behaviors.

### Role Tests

- New users receive the `none` role.
- Users can receive the `member` role when joining a group.
- Group owners receive the `manager` role.
- Only authorized operations can assign the `admin` role.
- Regular users cannot modify their own roles.
- Invalid role values are rejected.

### Group Isolation Tests

- Members can only view their own group's members.
- Members cannot access other groups' information.
- Managers can manage their own groups.
- Managers cannot access other groups' private information.
- Changing group IDs in URLs or requests must not bypass permissions.

### Security Tests

- Test unauthorized role modifications.
- Test privilege escalation attempts.
- Test IDOR vulnerabilities.
- Test unauthenticated access.
- Test unauthorized group operations.
- Test access through manipulated HTTP requests.

### General Testing Rules

- Use Pytest or Django's testing framework according to existing project conventions.
- Test successful and unsuccessful scenarios.
- Include important edge cases.
- Never remove or weaken existing tests just to make them pass.
- Never claim tests passed without actually executing them.

---

## 10. Documentation Guidelines

- Follow the existing project documentation structure.
- Update relevant documentation when role behavior changes.
- Document important permission rules.
- Avoid duplicating information unnecessarily.
- Document important architectural decisions.
- Do not create unnecessary documentation files.

---

## 11. AI Instructions

When working on this application, follow these instructions strictly.

### Before Coding

1. Read this README carefully.
2. Inspect the complete existing account application structure.
3. Read all relevant models, views, forms, URLs, and templates.
4. Inspect the existing group application and its relationships with the account application.
5. Understand the current authentication and authorization mechanisms.
6. Identify existing business logic before modifying anything.
7. Determine where the role field belongs according to the existing architecture.

### During Implementation

1. Follow the exact existing application structure.
2. Do not unnecessarily create, move, rename, or delete files.
3. Do not introduce new architectural patterns without justification.
4. Use Class-Based Views exclusively.
5. Preserve existing functionality.
6. Reuse existing models and relationships whenever possible.
7. Implement permissions on the backend.
8. Avoid modifying unrelated applications.
9. Do not assume relationships or behaviors that have not been verified.

### After Implementation

1. Review all modified files.
2. Verify role assignment and role transitions.
3. Verify group data isolation.
4. Test all important permissions.
5. Run relevant tests.
6. Report all modified and created files.
7. Report commands and tests actually executed.
8. Clearly mention unresolved issues.

### Uncertainty Handling

- Never guess about existing business logic.
- If the existing architecture conflicts with these requirements, explain the conflict before making structural changes.
- Ask for clarification when a critical requirement cannot be determined from the codebase.
- Never silently change existing architectural decisions.

---

## 12. Critical Rules

The following rules must never be violated without explicit user approval:

- Never delete existing models.
- Never delete existing database data.
- Never introduce a custom User model without explicit approval.
- Never change the existing application architecture unnecessarily.
- Never use Function-Based Views.
- Never allow ordinary users to assign roles.
- Never allow ordinary users to become admins.
- Never expose one group's private information to another group.
- Never allow members to view other groups' member lists.
- Never bypass backend authorization checks.
- Never overwrite or delete existing user changes.
- Never introduce unnecessary dependencies.

---

# Final Principle

Understand the existing architecture before making changes.

Preserve the existing structure. Enforce role-based permissions. Maintain strict group data isolation.

The objective is to build a secure, consistent, and maintainable account management system without unnecessarily changing the existing project architecture.

## Profile Management

The application must provide a Profile feature that allows users to manage their profile information and upload a personal profile picture.

### 1. Django Built-in User Model

- Use Django's built-in User model.
- Reference the user model through `settings.AUTH_USER_MODEL`.
- Do not create a custom User model.
- Do not modify Django's built-in User model.
- Use Django's built-in authentication and account management functionality.

### 2. Profile Model

Create a `Profile` model associated with the built-in User model using a `OneToOneField`.

The Profile model must contain:

| Field | Type | Description |
|---|---|---|
| id | PrimaryKey | Unique profile identifier |
| user | OneToOneField(AUTH_USER_MODEL) | Associated user |
| role | CharField | User's role |
| profile_picture | ImageField | User's profile picture |

### 3. Profile Picture Management

Users must be able to:

- Upload a profile picture.
- Change their existing profile picture.
- Remove their profile picture.
- View their current profile picture.

Requirements:

- Profile pictures must be optional.
- Use Django's built-in `ImageField`.
- Use Django's file storage mechanisms.
- Store uploaded images in a dedicated directory, such as `media/profile_pictures/`.
- Validate uploaded image files.
- Enforce an appropriate maximum file size.
- Do not trust user-provided filenames.
- Replace or remove old profile images safely.
- Provide a default profile image when no picture has been uploaded.

### 4. Profile Permissions

- Every authenticated user can view their own profile.
- Users can edit their own profile information.
- Users can upload, change, or remove only their own profile picture.
- Users must never be able to modify their own role through profile forms.
- Regular users must not be able to modify another user's profile.
- Profile visibility must respect the existing group data isolation rules.

### 5. Role Management

The `role` field must be managed separately from ordinary profile information.

Available roles:

- `none`
- `admin`
- `member`
- `manager`

Rules:

- New users must receive the default `none` role.
- Role changes must follow the existing role assignment rules.
- Never include the role field in user-editable profile forms.
- Only authorized backend operations can modify user roles.

### 6. Django Implementation Requirements

- Use Django's built-in `ImageField`.
- Use Django ModelForms where appropriate.
- Handle file uploads through `request.FILES`.
- Use `multipart/form-data` for upload forms.
- Use Django's existing file storage system.
- Use Class-Based Views (CBVs) exclusively.
- Do not use Function-Based Views (FBVs).
- Ensure profile creation follows the existing account creation architecture.
- Prevent duplicate Profile instances.
- Do not introduce unnecessary dependencies.

**Dependency Note:** Django's `ImageField` requires Pillow. Check existing dependencies before installing it.

### 7. Testing Requirements

Test the following scenarios:

- Profile creation for new users.
- Profile retrieval.
- Profile picture upload.
- Profile picture replacement.
- Profile picture removal.
- Invalid file uploads.
- Maximum file size validation.
- Unauthorized profile modifications.
- Attempts to modify the role through profile forms.
- Access to other users' profiles.