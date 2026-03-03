# SPEC-02: Document Upload & Management

> **Status:** ✅ Done  
> **Dependencies:** SPEC-01 (Auth) ✅  
> **Priority:** P0 — Critical Path  
> **Estimated effort:** 3–4 days

---

## Overview

Allow authenticated users to upload PDF research papers, store them in **Supabase Storage**, track their processing status, and manage (list, view, delete) their document library. This spec covers **only the upload and CRUD operations** — the actual PDF processing (text extraction, chunking, embedding) is handled by SPEC-03.

> **Storage Strategy:** Files are stored in a **private Supabase Storage bucket** (`documents`). All operations go through the backend using the Supabase **Service Role Key** — the frontend never accesses storage directly. This approach is chosen because the project already uses Supabase for authentication, and cloud storage avoids deployment issues with local filesystems.

---

## Database Changes

### Modify `documents` table

**File:** `src/models/db_scheams/document.py`

Add metadata columns needed for citation generation (SPEC-06):

| Column | Type | Constraints | New? | Purpose |
|---|---|---|---|---|
| `id` | UUID | PK, default uuid4 | ❌ | Primary key |
| `user_id` | UUID | FK → users.id, NOT NULL | ❌ | Owner |
| `file_name` | String(255) | NOT NULL | ❌ | Original filename |
| `file_path` | String(500) | NOT NULL | ❌ | Supabase Storage object path (e.g. `{user_id}/{document_id}.pdf`) |
| `file_size` | Integer | nullable | ✅ | File size in bytes |
| `total_pages` | Integer | nullable | ❌ | Total PDF pages |
| `title` | String(500) | nullable | ✅ | Paper title (from metadata or user) |
| `author` | String(500) | nullable | ✅ | Paper author(s) |
| `year` | String(10) | nullable | ✅ | Publication year |
| `journal` | String(500) | nullable | ✅ | Journal name |
| `doi` | String(255) | nullable | ✅ | Digital Object Identifier |
| `abstract` | Text | nullable | ✅ | Paper abstract |
| `status` | String(20) | default "uploading" | ❌ modified | processing state |
| `error_message` | Text | nullable | ✅ | Error details if failed |
| `created_at` | DateTime | default utcnow | ❌ | |
| `updated_at` | DateTime | auto-update | ❌ | |

### Status Flow

```
uploading → processing → ready
                ↓
              failed
```

| Status | Meaning |
|---|---|
| `uploading` | File received, not yet processed |
| `processing` | Ingestion pipeline running (SPEC-03) |
| `ready` | All chunks embedded, ready for queries |
| `failed` | Processing error — see `error_message` |

### Migration

After modifying the model:

```bash
alembic revision --autogenerate -m "add document metadata columns"
alembic upgrade head
```

---

## Pydantic Schemas

**New file:** `src/models/schemas/document_schemas.py`

### DocumentUploadResponse

```python
from pydantic import BaseModel
from datetime import datetime

class DocumentUploadResponse(BaseModel):
    id: str
    file_name: str
    file_size: int
    status: str
    message: str

    class Config:
        from_attributes = True
```

### DocumentListItem

```python
class DocumentListItem(BaseModel):
    id: str
    file_name: str
    title: str | None
    author: str | None
    year: str | None
    status: str
    total_pages: int | None
    file_size: int | None
    created_at: datetime

    class Config:
        from_attributes = True
```

### DocumentDetail

```python
class DocumentDetail(DocumentListItem):
    journal: str | None
    doi: str | None
    abstract: str | None
    error_message: str | None
    updated_at: datetime | None
    chunk_count: int  # number of chunks generated
```

### DocumentUpdateRequest

```python
class DocumentUpdateRequest(BaseModel):
    title: str | None = None
    author: str | None = None
    year: str | None = None
    journal: str | None = None
    doi: str | None = None
```

---

## API Endpoints

All endpoints require `Authorization: Bearer <access_token>` header.

---

### `POST /documents/upload`

Upload a PDF file.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` — PDF file (required)

**Validation Rules:**
- File extension must be `.pdf`
- File MIME type must be `application/pdf`
- File size ≤ 50 MB (configurable via `MAX_FILE_SIZE_MB`)
- File must not be empty (0 bytes)

**Success Response (201):**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "file_name": "deep_learning_medicine.pdf",
  "file_size": 2457600,
  "status": "processing",
  "message": "Upload successful. Processing started."
}
```

**Error Responses:**

| Status | Condition | Response |
|---|---|---|
| 400 | Not a PDF | `{"detail": "Only PDF files are accepted. Got: .docx"}` |
| 400 | Too large | `{"detail": "File too large. Maximum size is 50MB. Got: 67.3MB"}` |
| 400 | Empty file | `{"detail": "Uploaded file is empty"}` |
| 401 | No auth | `{"detail": "Not authenticated"}` |
| 500 | Storage error | `{"detail": "Failed to upload file to storage"}` |

**Side Effects:**
1. File uploaded to Supabase Storage bucket `documents` at path `{user_id}/{document_id}.pdf`
2. Document record created in DB with `file_path` = `{user_id}/{document_id}.pdf` and status `"processing"`
3. Ingestion task triggered (SPEC-03) — in v1 this is synchronous, in SPEC-08 it becomes async via Celery
4. If storage upload fails after DB record is created, record is cleaned up and error is returned

---

### `GET /documents/`

List all documents for the current user.

**Query Parameters:**
- `status` (optional): filter by status — `uploading`, `processing`, `ready`, `failed`

**Success Response (200):**
```json
{
  "documents": [
    {
      "id": "a1b2c3d4-...",
      "file_name": "deep_learning_medicine.pdf",
      "title": "Deep Learning in Medicine",
      "author": "Smith, John",
      "year": "2020",
      "status": "ready",
      "total_pages": 42,
      "file_size": 2457600,
      "created_at": "2026-03-01T10:30:00Z"
    },
    {
      "id": "b2c3d4e5-...",
      "file_name": "nlp_survey.pdf",
      "title": null,
      "author": null,
      "year": null,
      "status": "processing",
      "total_pages": null,
      "file_size": 1048576,
      "created_at": "2026-03-01T10:35:00Z"
    }
  ],
  "total": 2
}
```

---

### `GET /documents/{document_id}`

Get detailed information about a specific document.

**Success Response (200):**
```json
{
  "id": "a1b2c3d4-...",
  "file_name": "deep_learning_medicine.pdf",
  "title": "Deep Learning in Medicine",
  "author": "Smith, John",
  "year": "2020",
  "journal": "Journal of AI Research",
  "doi": "10.1234/jair.2020.001",
  "abstract": "This paper explores...",
  "status": "ready",
  "total_pages": 42,
  "file_size": 2457600,
  "chunk_count": 87,
  "error_message": null,
  "created_at": "2026-03-01T10:30:00Z",
  "updated_at": "2026-03-01T10:32:15Z"
}
```

**Error Responses:**

| Status | Condition | Response |
|---|---|---|
| 404 | Not found | `{"detail": "Document not found"}` |
| 403 | Not owner | `{"detail": "Access denied"}` |

---

### `PATCH /documents/{document_id}`

Update document metadata (user can manually fix/add title, author, etc.).

**Request Body:**
```json
{
  "title": "Deep Learning in Medical Imaging: A Survey",
  "author": "Smith, John A. and Doe, Jane B.",
  "year": "2020",
  "journal": "Journal of AI Research",
  "doi": "10.1234/jair.2020.001"
}
```

All fields are optional — only provided fields are updated.

**Success Response (200):**
```json
{
  "message": "Document updated successfully",
  "id": "a1b2c3d4-..."
}
```

**Error Responses:**

| Status | Condition | Response |
|---|---|---|
| 404 | Not found | `{"detail": "Document not found"}` |
| 403 | Not owner | `{"detail": "Access denied"}` |

---

### `DELETE /documents/{document_id}`

Delete a document, its file from Supabase Storage, and all associated chunks.

**Success Response (200):**
```json
{
  "message": "Document and all associated data deleted successfully"
}
```

**Side Effects:**
1. Delete PDF file from Supabase Storage bucket `documents` at path `{user_id}/{document_id}.pdf`
2. Delete all `document_chunks` where `document_id` matches (cascade)
3. Delete the `documents` record
4. If storage deletion fails, log a warning but still delete DB records (orphaned files can be cleaned up later)

**Error Responses:**

| Status | Condition | Response |
|---|---|---|
| 404 | Not found | `{"detail": "Document not found"}` |
| 403 | Not owner | `{"detail": "Access denied"}` |

---

## File Structure

### New Files to Create

| File | Purpose |
|---|---|
| `src/routes/document_routes.py` | Document API endpoints |
| `src/controllers/document_controller.py` | Document business logic |
| `src/models/schemas/document_schemas.py` | Pydantic request/response models |
| `src/helpers/storage.py` | Supabase Storage helper (upload, download, delete, signed URL) |

### Files to Modify

| File | Change |
|---|---|
| `src/models/db_scheams/document.py` | Add metadata columns (title, author, year, journal, doi, abstract, file_size, error_message) |
| `src/helpers/config.py` | Add `STORAGE_BUCKET`, `MAX_FILE_SIZE_MB` settings |
| `src/main.py` | Register document routes: `app.include_router(document_router)` |
| `.env` | Add `STORAGE_BUCKET=documents` and `MAX_FILE_SIZE_MB=50` |

---

## Config Additions

**File:** `src/helpers/config.py` — add to `Settings` class:

```python
# Supabase Storage
STORAGE_BUCKET: str = "documents"
MAX_FILE_SIZE_MB: int = 50
```

> **Note:** `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` should already exist in the config from SPEC-01 (Auth). These same credentials are reused for Storage operations.

---

## Business Rules

1. **File isolation:** Each user's files are stored under `{user_id}/` prefix in the Supabase Storage bucket. Users cannot access other users' files.
2. **Unique file storage:** Files are stored as `{user_id}/{document_id}.pdf` to avoid name collisions.
3. **Private bucket:** The `documents` bucket is **private** — no public access. All access goes through the backend using the Service Role Key.
4. **Status transitions:** Only valid transitions are:
   - `uploading` → `processing` (triggered by ingestion start)
   - `processing` → `ready` (ingestion complete)
   - `processing` → `failed` (ingestion error)
5. **Cascade delete:** Deleting a document deletes all its chunks from `document_chunks`.
6. **Metadata is optional:** Users can upload without providing metadata. The system will attempt to extract it from the PDF in SPEC-03, and users can manually edit it via PATCH.
7. **Storage cleanup:** If storage upload fails, the DB record is rolled back. If storage delete fails on document deletion, the DB records are still deleted (orphaned storage files are acceptable and can be cleaned up periodically).

---

## Dependencies (packages)

Already in `requirements.txt`:
- `python-multipart` — multipart form data parsing
- `supabase` — Supabase Python client (used for Auth in SPEC-01)

No new packages needed for this spec — the `supabase` client already includes Storage support.

---

## Test Scenarios

| # | Scenario | Expected Result |
|---|---|---|
| 1 | Upload valid 5MB PDF | 201, file saved, DB record created |
| 2 | Upload .docx file | 400, "Only PDF files are accepted" |
| 3 | Upload 60MB PDF | 400, "File too large" |
| 4 | Upload empty file | 400, "Uploaded file is empty" |
| 5 | Upload without auth token | 401, "Not authenticated" |
| 6 | List documents (has 3) | 200, returns array of 3 items |
| 7 | List documents (has 0) | 200, returns empty array |
| 8 | Get document by ID | 200, returns full detail |
| 9 | Get another user's document | 403, "Access denied" |
| 10 | Get non-existent document | 404, "Document not found" |
| 11 | Update document metadata | 200, metadata updated in DB |
| 12 | Delete document | 200, file deleted, DB record deleted, chunks deleted |
| 13 | Delete non-existent document | 404, "Document not found" |

---

## Acceptance Criteria

- [ ] `POST /documents/upload` accepts PDF files and uploads to Supabase Storage
- [ ] Non-PDF files are rejected with clear error message
- [ ] Files exceeding 50MB are rejected
- [ ] Empty files are rejected
- [ ] Document record is created in DB with status tracking
- [ ] `GET /documents/` returns all user's documents
- [ ] `GET /documents/{id}` returns full document details
- [ ] `PATCH /documents/{id}` allows updating metadata
- [ ] `DELETE /documents/{id}` removes file from Supabase Storage, DB record, and chunks
- [ ] Users cannot access other users' documents (403)
- [ ] Supabase Storage bucket `documents` is configured as private
- [ ] File is stored in Supabase Storage as `{user_id}/{document_id}.pdf`
- [ ] All endpoints require authentication
- [ ] Storage upload failures are handled gracefully with DB rollback
