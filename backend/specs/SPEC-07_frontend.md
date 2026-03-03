# SPEC-07: Frontend Integration

> **Status:** 🔲 Todo  
> **Dependencies:** SPEC-02 through SPEC-06 (all backend specs)  
> **Priority:** P0  
> **Estimated effort:** 2 weeks

---

## Overview

Build the complete frontend interface for ScholarGPT using Next.js 16, React 19, TypeScript, and Tailwind CSS 4. The frontend has four major areas:

1. **Document Upload Panel** — Drag & drop PDF upload with status tracking
2. **Chat Interface** — Question input, streaming AI answers, source attribution
3. **Citation Panel** — Expandable references with APA/MLA/BibTeX and copy buttons
4. **Chat History Sidebar** — List of past chats, create/delete/switch

```
┌───────────────────────────────────────────────────────────────┐
│  HEADER (Logo + User Menu)                                    │
├────────────┬──────────────────────────────────┬───────────────┤
│            │                                  │               │
│  Chat      │       CHAT MESSAGES              │  Document     │
│  History   │                                  │  Panel        │
│  Sidebar   │  ┌────────────────────────────┐  │               │
│            │  │ User: Question...          │  │  - doc1.pdf ✅│
│  + New Chat│  │ ────────────────────────── │  │  - doc2.pdf 🔄│
│            │  │ AI: Answer with [Source 1] │  │  - doc3.pdf ❌│
│  Chat 1    │  │                            │  │               │
│  Chat 2    │  │ ┌── Sources ─────────────┐ │  │  [Upload PDF] │
│  Chat 3    │  │ │ Source 1: Smith (2020) │ │  │               │
│            │  │ │ Source 2: Doe (2021)   │ │  │               │
│            │  │ │ [APA] [MLA] [BibTeX]  │ │  │               │
│            │  │ └────────────────────────┘ │  │               │
│            │  └────────────────────────────┘  │               │
│            │                                  │               │
│            │  ┌────────────────────────────┐  │               │
│            │  │ Ask a question...    [Send]│  │               │
│            │  └────────────────────────────┘  │               │
│            │                                  │               │
├────────────┴──────────────────────────────────┴───────────────┤
│  FOOTER                                                       │
└───────────────────────────────────────────────────────────────┘
```

---

## Tech Stack (Already Set Up)

| Technology | Version | Purpose |
|---|---|---|
| Next.js | 16.1.1 | Framework |
| React | 19.2.3 | UI library |
| TypeScript | 5.x | Type safety |
| Tailwind CSS | 4.x | Styling |
| Redux Toolkit | 2.x | State management |
| Axios | 1.x | HTTP client |
| Lucide React | 0.562 | Icons |

---

## Component Architecture

### New Components to Create

```
frontend/
├── app/
│   └── chat/
│       └── page.tsx                    # UPDATE: main chat page layout
├── components/
│   ├── chat/
│   │   ├── ChatSidebar.tsx             # NEW: chat history list
│   │   ├── ChatMessages.tsx            # NEW: message list display
│   │   ├── ChatInput.tsx               # NEW: question input box
│   │   ├── MessageBubble.tsx           # NEW: single message display
│   │   ├── SourcesPanel.tsx            # NEW: expandable sources per message
│   │   └── CitationBlock.tsx           # NEW: APA/MLA/BibTeX display + copy
│   └── documents/
│       ├── DocumentSidebar.tsx         # NEW: document list + upload
│       ├── DocumentUpload.tsx          # NEW: drag & drop upload zone
│       ├── DocumentItem.tsx            # NEW: single document with status
│       └── DocumentMetadataEdit.tsx    # NEW: edit metadata modal
├── store/
│   ├── store.ts                        # UPDATE: add new slices
│   ├── slices/
│   │   ├── authSlice.ts                # EXISTS
│   │   ├── chatSlice.ts                # NEW: chat state management
│   │   └── documentSlice.ts            # NEW: document state management
└── lib/
    └── api/
        ├── auth.ts                      # EXISTS
        ├── documents.ts                 # NEW: document API calls
        ├── chats.ts                     # NEW: chat API calls
        └── citations.ts                # NEW: citation API calls
```

---

## Component Specifications

### 1. ChatSidebar

**File:** `components/chat/ChatSidebar.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Show list of past chats, allow creating/switching/deleting |
| **Data source** | `GET /chats/` |
| **Actions** | New chat, switch chat, delete chat, rename chat |
| **State** | Active chat ID highlighted |
| **Position** | Left sidebar, 280px width, collapsible on mobile |

**UI Elements:**
- "New Chat" button at top (+ icon)
- Chat list sorted by newest first
- Each item: title (truncated), date
- Right-click or hover → delete button
- Active chat has accent background

---

### 2. ChatMessages

**File:** `components/chat/ChatMessages.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Display conversation messages in a scrollable list |
| **Data source** | `GET /chats/{id}` → messages array |
| **Behavior** | Auto-scroll to bottom on new message |
| **Loading state** | Skeleton loader while fetching |

---

### 3. MessageBubble

**File:** `components/chat/MessageBubble.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Render a single message (user or assistant) |
| **User message** | Right-aligned, teal background, short |
| **Assistant message** | Left-aligned, dark background, supports markdown |
| **Sources button** | "📚 View Sources (3)" expandable at bottom of assistant messages |
| **Markdown** | Parse bold, italic, headers, lists, code blocks in assistant responses |

---

### 4. SourcesPanel

**File:** `components/chat/SourcesPanel.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Show sources used for an AI response |
| **Trigger** | Click "View Sources" on an assistant message |
| **Data** | `source_chunks` from the message response |
| **Per source** | Source number, title, author, year, page, relevance score, excerpt |
| **Citation tabs** | APA / MLA / BibTeX tabs per source |
| **Copy button** | Copy citation to clipboard |

---

### 5. CitationBlock

**File:** `components/chat/CitationBlock.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Display a formatted citation with copy functionality |
| **Tabs** | APA, MLA, BibTeX |
| **Copy button** | Copies selected format to clipboard with feedback toast |
| **BibTeX display** | Monospace font, code block style |
| **Data source** | `GET /citations/messages/{message_id}` |

---

### 6. ChatInput

**File:** `components/chat/ChatInput.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Text input for asking questions |
| **Layout** | Full-width input with Send button |
| **Behavior** | Submit on Enter (Shift+Enter for newline) |
| **Disabled** | While AI is generating a response |
| **Placeholder** | "Ask a question about your research papers..." |
| **Validation** | Cannot submit empty question |

---

### 7. DocumentSidebar

**File:** `components/documents/DocumentSidebar.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Show uploaded documents and upload new ones |
| **Data source** | `GET /documents/` |
| **Position** | Right sidebar, 300px width, collapsible |
| **Polling** | Refresh every 5 seconds while any document is "processing" |

---

### 8. DocumentUpload

**File:** `components/documents/DocumentUpload.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Drag & drop zone for PDF upload |
| **Accept** | `.pdf` only |
| **Max size** | 50MB (show error if exceeded) |
| **Progress** | Upload progress bar |
| **Feedback** | Success toast, error toast |
| **API** | `POST /documents/upload` (multipart/form-data) |

---

### 9. DocumentItem

**File:** `components/documents/DocumentItem.tsx`

| Feature | Detail |
|---|---|
| **Purpose** | Single document in the list |
| **Status badge** | 🔄 Processing (amber), ✅ Ready (green), ❌ Failed (red) |
| **Info** | File name, page count, date |
| **Actions** | Delete, edit metadata |
| **Click** | Select/deselect for chat filtering |

---

## Redux Slices

### Document Slice

**File:** `store/slices/documentSlice.ts`

```typescript
interface DocumentState {
  documents: Document[];
  loading: boolean;
  uploading: boolean;
  uploadProgress: number;
  error: string | null;
  selectedDocumentIds: string[];  // for chat filtering
}

// Async Thunks:
// - fetchDocuments(): GET /documents/
// - uploadDocument(file): POST /documents/upload
// - deleteDocument(id): DELETE /documents/{id}
// - updateDocumentMetadata(id, data): PATCH /documents/{id}

// Actions:
// - toggleDocumentSelection(id)
// - clearSelection()
```

### Chat Slice

**File:** `store/slices/chatSlice.ts`

```typescript
interface ChatState {
  chats: ChatListItem[];
  activeChat: ChatDetail | null;  // includes messages
  loading: boolean;
  querying: boolean;  // true while AI is generating
  error: string | null;
}

// Async Thunks:
// - fetchChats(): GET /chats/
// - createChat(): POST /chats/
// - fetchChat(id): GET /chats/{id}
// - deleteChat(id): DELETE /chats/{id}
// - sendQuery(chatId, question, documentIds): POST /chats/{id}/query
// - renameChat(id, title): PATCH /chats/{id}

// Actions:
// - setActiveChat(chat)
// - appendMessage(message)
// - clearError()
```

---

## API Client Modules

### Document API

**File:** `lib/api/documents.ts`

```typescript
import axios from 'axios';

const API_BASE = process.env.NEXT_PUBLIC_API_URL;

export const documentsApi = {
  list: () =>
    axios.get(`${API_BASE}/documents/`, { headers: authHeaders() }),

  upload: (file: File, onProgress?: (percent: number) => void) =>
    axios.post(`${API_BASE}/documents/upload`, createFormData(file), {
      headers: { ...authHeaders(), 'Content-Type': 'multipart/form-data' },
      onUploadProgress: (e) => onProgress?.(Math.round((e.loaded * 100) / (e.total || 1))),
    }),

  get: (id: string) =>
    axios.get(`${API_BASE}/documents/${id}`, { headers: authHeaders() }),

  update: (id: string, data: Partial<DocumentMetadata>) =>
    axios.patch(`${API_BASE}/documents/${id}`, data, { headers: authHeaders() }),

  delete: (id: string) =>
    axios.delete(`${API_BASE}/documents/${id}`, { headers: authHeaders() }),
};
```

### Chat API

**File:** `lib/api/chats.ts`

```typescript
export const chatsApi = {
  list: () =>
    axios.get(`${API_BASE}/chats/`, { headers: authHeaders() }),

  create: (title?: string) =>
    axios.post(`${API_BASE}/chats/`, { title }, { headers: authHeaders() }),

  get: (id: string) =>
    axios.get(`${API_BASE}/chats/${id}`, { headers: authHeaders() }),

  delete: (id: string) =>
    axios.delete(`${API_BASE}/chats/${id}`, { headers: authHeaders() }),

  query: (chatId: string, question: string, documentIds?: string[]) =>
    axios.post(
      `${API_BASE}/chats/${chatId}/query`,
      { question, document_ids: documentIds },
      { headers: authHeaders() }
    ),

  rename: (id: string, title: string) =>
    axios.patch(`${API_BASE}/chats/${id}`, { title }, { headers: authHeaders() }),
};
```

### Citations API

**File:** `lib/api/citations.ts`

```typescript
export const citationsApi = {
  getForMessage: (messageId: string, format: string = 'all') =>
    axios.get(`${API_BASE}/citations/messages/${messageId}?format=${format}`, {
      headers: authHeaders(),
    }),

  export: (messageId: string, format: 'apa' | 'mla' | 'bibtex') =>
    axios.get(`${API_BASE}/citations/export?message_id=${messageId}&format=${format}`, {
      headers: authHeaders(),
      responseType: 'text',
    }),
};
```

---

## Page Layout

**File:** `app/chat/page.tsx`

The main chat page should use a 3-column layout:

```
Left sidebar (280px) | Main content (flex-1) | Right sidebar (300px)
ChatSidebar          | ChatMessages           | DocumentSidebar
                     | ChatInput              |
```

- Responsive: On mobile, sidebars become toggleable drawers
- Chat area takes remaining space
- Input fixed at bottom

---

## Design Guidelines

Follow the existing Medical AI design system already established in the project:

| Element | Style |
|---|---|
| Primary color | Teal (from existing auth pages) |
| Background | Dark mode (dark gray/navy) |
| Message bubbles | User: teal, Assistant: dark card with border |
| Source badges | Subtle tags with relevance score |
| Upload zone | Dashed border, teal accent on hover |
| Status badges | Green (ready), Amber (processing), Red (failed) |
| BibTeX blocks | Monospace font, copy button |
| Animations | Smooth slide-in for new messages |

---

## Test Scenarios

| # | Scenario | Expected |
|---|---|---|
| 1 | Upload PDF via drag & drop | File uploaded, appears in list with "processing" status |
| 2 | Upload non-PDF | Error toast shown |
| 3 | Document finishes processing | Status changes to "ready" (green badge) |
| 4 | Create new chat | Empty chat opens, input focused |
| 5 | Send question | User message appears, loading indicator, AI response appears |
| 6 | Click "View Sources" | Sources panel expands with references |
| 7 | Copy BibTeX | Copied to clipboard, toast confirmation |
| 8 | Switch between chats | Messages update to selected chat |
| 9 | Delete chat | Chat removed from sidebar |
| 10 | Delete document | Document removed from list |
| 11 | Filter by document | Only results from selected documents |
| 12 | Responsive: mobile view | Sidebars collapse to toggleable drawers |
| 13 | Empty state: no documents | Shows "Upload your first paper" prompt |
| 14 | Empty state: no chats | Shows "Start a new conversation" prompt |

---

## Acceptance Criteria

- [ ] Document upload via drag & drop works with progress indicator
- [ ] Document list shows status badges (processing/ready/failed)
- [ ] Documents can be deleted and metadata can be edited
- [ ] Chat sidebar lists all chats, newest first
- [ ] New chat can be created
- [ ] Chat can be renamed and deleted
- [ ] Questions can be sent and AI answers are displayed
- [ ] Assistant messages show "View Sources" button
- [ ] Sources panel shows title, author, year, page, relevance, excerpt
- [ ] Citation tabs (APA/MLA/BibTeX) work correctly
- [ ] Copy-to-clipboard works for all citation formats
- [ ] Chat input is disabled while AI is generating
- [ ] Auto-scroll to latest message
- [ ] Document selection filters chat results
- [ ] Responsive layout (desktop + tablet + mobile)
- [ ] Empty states are handled with helpful prompts
- [ ] Loading states use skeleton loaders
- [ ] Error states show clear error messages
