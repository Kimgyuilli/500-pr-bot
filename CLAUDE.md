# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

500 Error Auto-Fix Bot: A FastAPI bot that automatically analyzes/fixes code and creates GitHub PRs when 500 errors occur in a Spring Boot app.

Detailed plan: `docs/Error bot project plan.md`

## Tech Stack

- **Bot**: Python + FastAPI (async)
- **AI**: OpenAI API (gpt-4o-mini) — `ai_service.py`에서 교체 가능
- **VCS**: GitHub REST API (PyGithub)
- **Notifications**: Discord Webhook

## Core Flow

```
Spring Boot 500 error → POST /webhook/error → FastAPI bot
  → Discord alert → GitHub code fetch → AI analyze/fix → Create PR → Discord completion alert
```

## Coding Guidelines

**Stop and ask when uncertain.**
- State assumptions explicitly. Present options when multiple interpretations exist.
- Suggest simpler approaches when they exist.

**Write the minimum code that solves the problem.**
- No unrequested features, abstractions, configurability, or error handling for impossible scenarios.
- If 200 lines can be 50, rewrite it.

**Change only what was requested.**
- No adjacent code improvements, style changes, or refactoring. Match existing style.
- Only remove dead code YOUR changes created. Mention pre-existing dead code, don't delete it.

**Turn tasks into verifiable goals.**
- For multi-step tasks, plan as `[step] → verify: [check]`.

## Language

Project docs and commit messages are written in Korean.
