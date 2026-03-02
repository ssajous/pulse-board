# PRD Configuration

## Feature
- **Feature Name**: slido-parity
- **Feature Slug**: slido-parity
- **Description**: Audience interaction features achieving parity with Slido's free tier

## Project
- **Project Name**: Pulse Board
- **Language**: Python 3.13+ (backend), TypeScript (frontend)
- **Package Manager**: uv (backend), npm (frontend)
- **Framework**: FastAPI (backend), React 19 + MobX (frontend)
- **Database**: PostgreSQL with SQLAlchemy 2.0 + Alembic
- **Real-time**: WebSockets (already implemented)

## Status
- **Status**: DRAFT
- **Version**: 0.1.0
- **Created**: 2026-03-02
- **Last Updated**: 2026-03-02

## Constraints
- Preserve existing single-board mode as quick-start default
- Retain downvote functionality (Pulse Board differentiator)
- Retain browser fingerprinting for anonymous identity
- Scale target: 100 concurrent participants per event
- Follow existing onion architecture (domain/application/infrastructure/presentation)
- Follow MVVM pattern with MobX on frontend
