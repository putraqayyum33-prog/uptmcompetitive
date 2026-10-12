# UPTM Secure Competitive Gaming Platform — Agent Rules

## Project Overview

This is the **UPTM Secure Competitive Gaming Platform**, a full-stack web application for the Universiti Poly-Tech Malaysia (UPTM) E-Sports Club. It provides secure scrimmage matchmaking, tournament management, and player profile tracking for campus esports (primarily Mobile Legends: Bang Bang).

## Tech Stack (Current Stack)

- **Backend**: Python 3.14 + Flask 3.x + Flask-SQLAlchemy + Flask-Login + Flask-WTF + Werkzeug
- **Frontend**: HTML5 + Jinja2 Templates + Bootstrap 5.3 + Bootstrap Icons + Custom Dark Esports Theme
- **Database**: SQLite (`instance/uptm_esports.db`)
- **Security**: AES-256-GCM encryption for PII, SHA-256 append-only audit chaining, institutional email domain restriction (`@student.uptm.edu.my`)
- **Testing**: Python unittest suite (`tests/test_app.py`)

## Architecture Rules

### Frontend (`apps/web/`)

- Use the **Next.js App Router** — no Pages Router
- Prefer **React Server Components** by default; only add `"use client"` when interactivity is needed
- Use **Zustand** for client-side global state — never Redux or plain Context for complex state
- Use **TanStack Query** for server state and data fetching on the client
- Use **React Hook Form + Zod** for all forms — no uncontrolled forms
- Use **Shadcn/ui** components — do not install other component libraries (no MUI, Ant Design, Chakra)
- All components must be in `src/components/` organized by feature folders
- Shared types go in `packages/shared/` — never duplicate type definitions

### Backend (`apps/api/`)

- Follow a **layered architecture**: Routes → Controllers → Services → Prisma Models
- Controllers handle request/response only — business logic lives in Services
- Use **Zod schemas** to validate ALL request bodies, query params, and route params
- Every route must go through the middleware stack: `authenticate → authorize → validate → handler`
- Use **Prisma** for ALL database interactions — never write raw SQL strings
- Environment variables via `dotenv` — never hardcode secrets
- All async route handlers must be wrapped in error-catching middleware

### Database

- Use **Prisma Migrate** for all schema changes — never modify the database manually
- Use **soft deletes** (`deletedAt` timestamp) for Users, Teams, and Tournaments — never hard delete
- Add database indexes on frequently queried columns (email, status, teamId, tournamentId)
- All timestamp fields use `DateTime @default(now())` or `@updatedAt`

## Security Mandates (NON-NEGOTIABLE)

These rules must NEVER be violated under any circumstances:

1. **Tokens in HttpOnly Cookies ONLY** — never localStorage, never sessionStorage, never expose JWT to client JS
2. **Server-side RBAC on EVERY protected endpoint** — never rely on frontend role checks alone
3. **Prevent BOLA** — always verify the requesting user owns or has permission to access the target resource. Never trust client-provided user IDs.
4. **Encrypt PII at rest** — student IDs, phone numbers, and any PDPA-sensitive fields must be AES-256 encrypted before database storage
5. **Parameterized queries only** — enforced by Prisma, but explicitly: no string concatenation in any query
6. **Input sanitization** — use Zod validation on server, DOMPurify on any rendered user content
7. **Rate limiting** — all auth endpoints: 100 req/15min per IP. General API: 1000 req/15min
8. **Audit logging** — every admin action (role change, ban, tournament edit, data export) MUST be recorded in the append-only audit log with SHA-256 hash chain
9. **Institutional email gating** — only `@student.uptm.edu.my` and `@uptm.edu.my` email domains may register
10. **CORS whitelist** — only allow the frontend origin, never use `*`

## Coding Standards

### TypeScript

- **Strict mode** in all `tsconfig.json` files (`"strict": true`)
- No `any` type — use `unknown` and narrow, or define proper types
- All functions must have explicit return types
- Use `interface` for object shapes, `type` for unions/intersections
- Use `const` assertions and enums for fixed sets of values (roles, statuses)

### Naming Conventions

- **Files**: `kebab-case.ts` for utilities, `PascalCase.tsx` for React components
- **Variables/Functions**: `camelCase`
- **Types/Interfaces/Enums**: `PascalCase`
- **Constants**: `SCREAMING_SNAKE_CASE`
- **Database tables**: `PascalCase` (Prisma default)
- **API routes**: `/api/v1/kebab-case` (RESTful)

### API Design

- Follow **RESTful conventions**: `GET /api/v1/teams`, `POST /api/v1/teams`, `PATCH /api/v1/teams/:id`
- Use **HTTP status codes correctly**: 200 (OK), 201 (Created), 400 (Bad Request), 401 (Unauthorized), 403 (Forbidden), 404 (Not Found), 409 (Conflict), 429 (Too Many Requests), 500 (Internal Server Error)
- Return consistent JSON response shape: `{ success: boolean, data?: T, error?: { code: string, message: string } }`
- Paginate all list endpoints: `?page=1&limit=20`
- Version all API routes under `/api/v1/`

### Error Handling

- NEVER expose raw error messages, stack traces, or internal details to the client
- Use a centralized error handler middleware
- Log full error details server-side with Winston
- Return user-friendly error messages with appropriate HTTP status codes

## Git & Commit Rules

- Use **Conventional Commits**: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, `security:`
- Each commit should be atomic — one logical change per commit
- Always run `lint` and `type-check` before committing

## Testing Requirements

- **Unit tests** (Vitest): All service-layer functions, utility functions, and validation schemas
- **API integration tests** (Supertest): All CRUD endpoints, auth flows, RBAC enforcement
- **E2E tests** (Playwright): Login flow, team creation, scrim request flow, admin panel
- Minimum coverage target: 80% for services layer
- Tests must pass before any merge

## Documentation

- Every exported function and class must have JSDoc comments
- API endpoints documented via Swagger/OpenAPI decorators
- README.md in each app/package directory explaining setup and usage
- Environment variable documentation in `.env.example`

## Performance

- Use Next.js Image component for all images (auto optimization)
- Implement skeleton loaders for data-heavy pages
- Use React.lazy + Suspense for code splitting on heavy components
- Database queries must use `select` to pick only needed fields — no `SELECT *`
- Implement proper caching headers on static assets
