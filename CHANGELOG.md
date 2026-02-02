# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.1.0] - 2026-02-02

### Added

- **Routing**: `ZodiacAPIRouter` with automatic `Response[T]` wrapping using Pydantic v2 native generics
- **Response**: Standard API response model `Response[T]` with `code`, `data`, `message` fields
- **Exceptions**: `ZodiacException` hierarchy (`NotFoundException`, `BadRequestException`, `ForbiddenException`, `UnauthorizedException`, `ConflictException`)
- **Exception Handlers**: Centralized handlers for `ZodiacException`, `RequestValidationError`, and generic exceptions
- **Middleware**: `TraceIDMiddleware` for request tracing, `AccessLogMiddleware` for structured access logging
- **Logging**: `setup_loguru()` with JSON format support and Trace ID injection
- **Context**: `trace_id` context variable for cross-cutting request tracing
- **Config**: `BaseAppSettings` with environment-based configuration using Pydantic Settings
- **Database**:
  - `DatabaseManager` singleton for async SQLAlchemy engine/session management
  - `BaseSQLRepository` with session context manager
  - SQLModel mixins: `IntIDMixin`, `UUIDMixin`, `SQLDateTimeMixin`
- **HTTP**: `HttpClient` async wrapper around httpx with automatic Trace ID propagation
- **Pagination**: `PageParams` request model and `PagedResponse[T]` response model
- **Schemas**: Pydantic mixins: `IntIDSchemaMixin`, `UUIDSchemaMixin`, `DateTimeSchemaMixin`
- **Benchmarks**: Performance benchmarks for routing overhead and internal operations
- **Documentation**: MkDocs-based API reference and user guide
