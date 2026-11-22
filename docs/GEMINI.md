# GEMINI.md

# Project Development Guidelines

## 1. Project Overview

-- **Project Name:** projectManagement
-- **Description:** A web-based project management application.
-- **Main Goal:** Building a production-grade project management platform with powerful features, excellent performance, security, and maintainable architecture.
-- **Project Status:** Development

--**Project Goal:**
The project is intended to become a complete Project Management Platform with the following features:

- **Chat:** Real-time messaging using WebSockets.
- **Project Tasks:** Project and task management.
- **Ticket System:** Ticket creation and management.
- **Emails:** Email management and communication.
- **Simple Notes:** A simple note-taking system.
- **Customer Documents:** Customer document management.
- **Monitoring:** System and activity monitoring.
- **Colleagues:** Team members and colleague management.

The goal is to implement all these features completely and correctly, following production-grade standards. Every feature must be fully functional, reliable, secure, and properly implemented for real-world production use.

### Core Principles

- Prioritize correctness, maintainability, and security.
- Build features that solve real problems.
- Avoid unnecessary complexity.
- Think about scalability when making architectural decisions.
- Maintain consistency throughout the project.

---

## 2. Technology Stack

The project currently uses the following technologies:

| Component | Technology |
|---|---|
| Backend | Django |
| Inviorment variable | environs[django] |
| Frontend | HTML, CSS, JavaScript |
| Database | PostgreSQL |
| Infrastructure | Docker |
| Unit & Integration Testing | Pytest / Django Test Framework  |
| Load Testing | Locust |

### Technology Rules

- Do not introduce new technologies without a clear technical reason.
- Prefer existing dependencies and built-in Django features.
- Do not replace existing technologies without explicit approval.
- Check package compatibility with the current Python and Django versions before installation.

---

## 3. Project Architecture

### General Rules

- Keep each Django application responsible for a specific domain.
- Follow the existing architectural patterns.
- Avoid unnecessary coupling between applications.
- Reuse existing components and services when appropriate.
- Maintain clear boundaries between application responsibilities.
- Avoid circular imports.
- Do not introduce unnecessary architectural patterns.

### Architecture Decisions

- Do not introduce Repository Pattern, Service Layer, or other architectural abstractions without a clear justification.
- Do not move existing business logic between layers without understanding its dependencies.
- Prefer Django's built-in capabilities whenever they are sufficient.
- Before changing the architecture, analyze the impact on existing applications.

---

## 4. Coding Standards

### General

- Write clean, readable, and maintainable code.
- Follow official Python and Django conventions.
- Use meaningful variable, function, and class names.
- Avoid unnecessary abstractions.
- Avoid code duplication.
- Keep functions and classes focused on a single responsibility.
- Add comments only when the logic is not self-explanatory.
- Prefer simple solutions over unnecessary complexity.
- Use type hints when they improve readability and maintainability.

### Django Views

- Always use Class-Based Views (CBVs).
- Never use Function-Based Views (FBVs).
- Prefer Django Generic Class-Based Views when appropriate.
- Use Mixins when they provide a clear benefit.
- Keep views focused on handling HTTP requests and responses.
- Avoid duplicating business logic across views.

### Django Models

- Use meaningful model and field names.
- Define explicit relationships and related_name values.
- Implement meaningful __str__ methods.
- Use appropriate field types and constraints.
- Avoid unnecessary model methods and properties.
- Keep model responsibilities clear.

### Frontend

- Write semantic HTML.
- Keep CSS organized and reusable.
- Use JavaScript only where necessary.
- Avoid unnecessary frontend dependencies.
- Maintain consistent UI behavior across the application.
- Consider accessibility and responsive design.

---

## 5. Development Rules

Before implementing any feature:

1. Inspect the existing project structure.
2. Read relevant models, views, forms, templates, and URLs.
3. Understand existing business logic.
4. Identify dependencies and potential side effects.
5. Determine the simplest maintainable implementation.

During development:

- Avoid modifying unrelated files.
- Preserve existing functionality unless explicitly requested otherwise.
- Do not rewrite working code without a valid reason.
- Do not assume a feature exists without checking the codebase.
- Make incremental and focused changes.
- Reuse existing functionality instead of duplicating it.
- Follow established naming and file organization conventions.
- Do not create duplicate files, classes, or functions.

After development:

- Review all modified files.
- Check for possible regressions.
- Run relevant tests.
- Report unresolved problems.

---

## 6. Security Rules

- Never hardcode secrets, passwords, or API keys.
- Use environment variables for sensitive configuration.
- Use the `environs` package for environment variable management.
- Follow the existing environment configuration conventions.
- Never commit `.env` files.
- Validate all external input.
- Follow secure authentication and authorization practices.
- Never expose sensitive information in responses or logs.
- Apply the principle of least privilege.
- Protect against CSRF, XSS, SQL Injection, and other common web vulnerabilities.
- Never trust client-side validation alone.
- Check object-level permissions before allowing access to sensitive resources.

---

## 7. Database Guidelines

- Use PostgreSQL as the primary database.
- Use Django ORM unless raw SQL is technically justified.
- Use appropriate field types and constraints.
- Define relationships explicitly.
- Add indexes when justified by query patterns.
- Avoid unnecessary database queries.
- Prevent N+1 query problems.
- Use `select_related()` and `prefetch_related()` when appropriate.
- Use `transaction.atomic()` for operations requiring database consistency.
- Preserve existing data when modifying schemas.
- Use Django migrations for schema changes.
- Never manually modify production database schemas.

### Data Integrity

- Consider database-level constraints for important business rules.
- Prevent inconsistent or invalid relationships.
- Handle concurrent database operations when necessary.
- Never perform destructive database operations without explicit approval.

---

## 8. API Guidelines

When developing or modifying APIs:

- Follow consistent naming conventions.
- Follow REST principles when applicable.
- Use appropriate HTTP methods and status codes.
- Validate request data.
- Return predictable response structures.
- Handle errors consistently.
- Apply appropriate authentication and authorization.
- Avoid exposing internal implementation details.

### API Documentation

- Maintain API documentation in `API.md`.
- Document new endpoints.
- Update documentation when existing endpoints change.
- Document request parameters, response structures, status codes, and authentication requirements.
- Do not document endpoints that do not actually exist.

---

## 9. Testing Guidelines

- Write tests for every new feature.
- Test important edge cases.
- Test successful and unsuccessful scenarios.
- Test authentication and authorization where applicable.
- Test database relationships and constraints.
- Verify existing functionality after modifications.
- Do not remove or weaken existing tests just to make them pass.
- Never claim tests passed without actually running them.

### Testing Strategy

- Use Pytest or Django's testing framework according to existing project conventions.
- Use Locust for load testing when performance or concurrency needs to be evaluated.
- Do not run unnecessary load tests for every minor change.

---

## 10. Performance Guidelines

- Avoid unnecessary database queries.
- Optimize ORM operations.
- Use pagination for large datasets.
- Avoid loading unnecessary database fields.
- Use caching when there is a measurable benefit.
- Consider database indexing for frequently queried fields.
- Avoid premature optimization.
- Consider performance implications when implementing large-scale features.

---

## 11. Dependency Management

- Check existing dependencies before installing new packages.
- Avoid unnecessary dependencies.
- Prefer established and maintained libraries.
- Do not upgrade packages without a clear reason.
- Check compatibility before installing packages.
- Keep dependency files synchronized.
- Never remove an existing dependency without checking its usage.

---

## 12. Docker & Deployment

- Follow existing Docker configurations.
- Keep Dockerfiles simple and maintainable.
- Use environment variables for configuration.
- Never store credentials inside Docker images.
- Keep development and production configurations separate.
- Avoid unnecessary changes to existing Docker services.
- Consider security and resource efficiency in production configurations.

---

## 13. AI Instructions

When working on this project, follow these instructions:

### Understanding

1. Read and understand relevant files before editing.
2. Follow the existing project architecture.
3. Do not invent requirements or undocumented behavior.
4. Ask questions when critical requirements are ambiguous.
5. If something is unknown, do not guess. Investigate the codebase or ask for clarification.

### Implementation

6. Prefer minimal and maintainable changes.
7. Explain important architectural decisions.
8. Avoid unnecessary modifications.
9. Preserve existing behavior.
10. Do not introduce new dependencies or technologies without justification.

### Verification

11. Review all modified files.
12. Report all modified and created files.
13. Report commands and tests actually executed.
14. Clearly mention unresolved issues.
15. Never claim something works without verification.

### Communication

16. Be direct, precise, and technically accurate.
17. Explain important trade-offs when multiple solutions exist.
18. Do not hide potential problems or limitations.
19. Ask questions instead of making assumptions when important information is missing.

---

## 14. Documentation Guidelines

- Keep documentation accurate and up to date.
- Update relevant documentation when changing application behavior.
- Use `API.md` for API documentation.
- Avoid duplicating documentation unnecessarily.
- Document important architectural decisions.
- Do not create documentation files without a clear purpose.

---

## 15. Critical Rules

These rules must never be violated without explicit user approval:

- Never delete existing models.
- Never delete existing database data.
- Never perform destructive database migrations.
- Never modify production database settings.
- Never overwrite or delete existing user changes.
- Never force-push to Git repositories.
- Never install dependencies without checking existing alternatives.
- Never introduce a new architectural pattern without justification.
- Never modify unrelated application functionality.
- Never expose secrets or credentials.

## Documentation Organization

- Keep global project documentation inside the `docs/` directory.
- Do not create separate documentation files for every Django application by default.
- Create app-specific documentation only when an application has complex business logic or independent architectural responsibilities.
- Keep documentation synchronized with code changes.
- Avoid duplicating information across documentation files.
- Before creating documentation, check whether the information already exists.
- Use clear references between related documentation files.

# Final Principle

Understand first. Analyze carefully. Implement minimally. Test thoroughly.

The primary objective is not simply to write code, but to build a reliable, secure, maintainable, and production-grade project management application.

evey app have readme (document of app , model structure ,  logic , api  )

