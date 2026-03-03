# 📦 ScholarGPT — Spec Kits

> All specifications for the ScholarGPT project.  
> Each spec is **self-contained** and **implementation-ready**.

## Status Dashboard

| Spec | Name | Status | Dependencies |
|---|---|---|---|
| [SPEC-01](./SPEC-01_auth.md) | Authentication System | ✅ Complete | None |
| [SPEC-02](./SPEC-02_document-upload.md) | Document Upload & Management | 🔲 Todo | SPEC-01 |
| [SPEC-03](./SPEC-03_ingestion-pipeline.md) | Ingestion Pipeline | 🔲 Todo | SPEC-02 |
| [SPEC-04](./SPEC-04_retrieval-layer.md) | Retrieval Layer | 🔲 Todo | SPEC-03 |
| [SPEC-05](./SPEC-05_chat-system.md) | Chat System & LLM | 🔲 Todo | SPEC-04 |
| [SPEC-06](./SPEC-06_citation-engine.md) | Citation & Reference Engine | 🔲 Todo | SPEC-05 |
| [SPEC-07](./SPEC-07_frontend.md) | Frontend Integration | 🔲 Todo | SPEC-02 — SPEC-06 |
| [SPEC-08](./SPEC-08_async-optimization.md) | Async & Optimization | 🔲 Todo | SPEC-03 |
| [SPEC-09](./SPEC-09_testing.md) | Testing Strategy | 🔲 Todo | Runs with each spec |

## Dependency Graph

```
SPEC-01 (Auth) ✅
    │
    ▼
SPEC-02 (Upload) ───────────────────────┐
    │                                    │
    ▼                                    │
SPEC-03 (Ingestion) ──► SPEC-08 (Async) │
    │                                    │
    ▼                                    │
SPEC-04 (Retrieval)                      │
    │                                    │
    ▼                                    │
SPEC-05 (Chat + LLM) ◄──────────────────┘
    │
    ▼
SPEC-06 (Citations)
    │
    ▼
SPEC-07 (Frontend) ← depends on all above
```

## How to Use

1. **Pick the next spec** with no unfinished dependencies
2. **Read it** — it contains everything you need
3. **Build it** — follow the file structure and code examples
4. **Verify it** — check every Acceptance Criteria item
5. **Mark it ✅** — update this dashboard and move to the next
