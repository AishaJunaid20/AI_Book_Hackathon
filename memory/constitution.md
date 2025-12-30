<!-- SYNC IMPACT REPORT:
Version change: N/A -> 1.0.0
Modified principles: N/A (new constitution)
Added sections: Core Principles for AI-authored book project
Removed sections: N/A
Templates requiring updates:
  - .specify/templates/plan-template.md ✅ updated
  - .specify/templates/spec-template.md ✅ updated
  - .specify/templates/tasks-template.md ✅ updated
  - .specify/templates/commands/*.md ⚠ pending
Follow-up TODOs: None
-->
# AI-authored book with embedded RAG chatbot Constitution

## Core Principles

### Spec-first
All behavior defined by specs. Every feature and functionality must be clearly specified before implementation. No code without a corresponding specification.

### Accuracy
Original, clear, technically correct content. All book content must be factually accurate, technically sound, and properly sourced. No assumptions, no external knowledge beyond indexed content.

### Reproducibility
Zero hallucinations. The RAG chatbot must answer strictly from indexed content. If answer missing: "Insufficient information in selected content." All processes must be reproducible from the repository.

### Developer-focused
Built with Docusaurus and deployed to GitHub Pages. Technology stack: Docusaurus, GitHub Pages, FastAPI, OpenAI Agents/ChatKit, Qdrant Cloud, Neon Postgres. Tools and processes must be developer-friendly and well-documented.

### Zero hallucinations
Chatbot answers strictly from indexed content. No assumptions, no external knowledge. If answer missing: "Insufficient information in selected content." Strict adherence to content boundaries.

### Complete Integration
RAG functionality works correctly with text-selection querying. Book deployed with fully reproducible build process. All components must work together seamlessly.

## Technology Stack Requirements
The project must use the specified technology stack: Docusaurus for documentation, GitHub Pages for deployment, FastAPI for backend services, OpenAI Agents/ChatKit for AI functionality, Qdrant Cloud for vector storage, and Neon Postgres for relational data. Any deviations require explicit approval and documentation.

## Development Workflow
All development follows Spec-Kit Plus methodology. Features are implemented based on specifications in the specs/ directory. Code must pass all tests before merging. Documentation must be updated with each feature addition.

## Governance
This constitution supersedes all other development practices. All pull requests and code reviews must verify compliance with these principles. Any architectural decisions that impact these principles require explicit amendment to this constitution.

**Version**: 1.0.0 | **Ratified**: 2025-12-23 | **Last Amended**: 2025-12-23