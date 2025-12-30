---
id: 1
title: "Create Project Constitution"
stage: constitution
date_iso: "2025-12-23"
surface: "agent"
model: "claude-sonnet-4-5-20250929"
feature: "none"
branch: "master"
user: "FCC"
command: "sp.constitution"
labels: ["constitution", "setup", "project"]
links:
  spec: null
  ticket: null
  adr: null
  pr: null
files_yaml:
  - ".specify/memory/constitution.md"
tests_yaml: []
---

## Prompt Text
```
Project: AI-authored book with embedded RAG chatbot

Goal:
Write and publish a technical book using Claude Code + Spec-Kit Plus, built with Docusaurus and deployed to GitHub Pages, including a RAG chatbot that answers only from book content or user-selected text.

Principles:
Spec-first · Accurate · Reproducible · Developer-focused · Zero hallucinations

Stack:
Docusaurus · GitHub Pages · FastAPI · OpenAI Agents/ChatKit · Qdrant Cloud · Neon Postgres

Rules:

All behavior defined by specs

Original, clear, technically correct content

Chatbot answers strictly from indexed content

If answer missing: "Insufficient information in selected content."

No assumptions, no external knowledge

Done When:
Book deployed · RAG works correctly · Text-selection querying works · Fully reproducible from repo
```

## Response Text
Created project constitution with core principles for the AI-authored book with embedded RAG chatbot project, including Spec-first, Accuracy, Reproducibility, Developer-focused, Zero hallucinations, and Complete Integration principles.

## Outcome
Project constitution successfully created at .specify/memory/constitution.md with version 1.0.0, incorporating all specified principles and requirements.

## Evaluation
The constitution properly reflects the project goals, principles, and technology stack. All principles are clearly defined with actionable descriptions, and governance procedures are established.