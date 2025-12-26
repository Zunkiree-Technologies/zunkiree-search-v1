# Zunkiree Search v1 — Build Specification

> This is written like an internal engineering + product spec for a serious SaaS company.
> It includes vision, scope, tech stack, system architecture, system design, task breakdown, guardrails, and pilot setup.

---

| Field | Value |
|-------|-------|
| **Product** | Zunkiree Search (Module of Zunkiree AI Platform) |
| **Company** | ZunkireeLabs |
| **Stage** | v1 / Pilot / Early Access |
| **Mode** | Fast, real, production-grade |
| **Built with** | Claude Code (AI coding agent) |

---

## 1. Product Context (Read First)

Zunkiree Search is an AI-native, embeddable search and interaction widget that allows users to ask natural-language questions and receive accurate, contextual answers based on a business's own data.

**This is not a chatbot demo.**
**This is infrastructure-grade software, starting small.**

### Product Principles (Non-Negotiable)

- Product > project
- Quality > feature count
- Infrastructure > gimmicks
- Horizontal > niche (for v1)
- Fast shipping > over-engineering

---

## 2. v1 Goals (Locked)

Zunkiree Search v1 must:

- Be embeddable on any website via a script
- Answer real user questions using business data
- Work for 3 pilot customers:
  - Admizz Education
  - Khems Cleaning
  - Guntabya (OTA)
- Feel fast, calm, and trustworthy
- Require minimal setup per customer

> v1 does not aim to scale to thousands of customers yet.

---

## 3. v1 Feature Scope (Locked)

### Included

#### Customer-Facing

- Search / chat widget
- Natural language questions
- Contextual answers
- Graceful fallback ("I don't have that info yet")
- Follow-up suggestions (optional, simple)

#### Backend

- Website + document ingestion
- Chunking + embeddings
- Retrieval-augmented generation (RAG)
- Prompt orchestration
- Response validation
- Logging (internal)

#### Admin (Internal-Only)

- Upload documents
- Trigger re-index
- Configure:
  - Brand name
  - Tone (formal / neutral)
  - Allowed topics

### Excluded (Do Not Build)

- Analytics dashboards
- Self-serve SaaS UI
- Payments
- User accounts
- Industry-specific logic
- Complex permissions
- Heavy UI theming

---

## 4. Technology Stack (Approved)

### AI & Intelligence

| Component | Technology |
|-----------|------------|
| LLM | OpenAI gpt-4o-mini (default) / gpt-4o (premium) - See [LLM Strategy](docs/llm-abstraction.md) |
| Embeddings | text-embedding-3-large |
| RAG framework | LlamaIndex or LangChain (helpers only) |

> **Note:** Model is configurable via environment variables. Accuracy comes from RAG quality, not expensive models.

### Vector Database

- **Pinecone** (starter/free tier)
- Namespace per customer

### Backend

- **Python + FastAPI**
- Async endpoints
- Clean service boundaries

### Data Storage

**PostgreSQL** for:
- Customers
- Domains
- Widget config
- Ingestion metadata

### Object Storage

- S3-compatible (Cloudflare R2 / Supabase Storage)

### Frontend (Widget)

- React + Vite
- Compiled to embeddable JS bundle
- Minimal, neutral UI

### Hosting & Infra

| Service | Provider |
|---------|----------|
| API | Railway / Fly.io |
| Frontend | Vercel / Cloudflare Pages |
| CDN & Security | Cloudflare (free) |
| Secrets | Environment variables |

---

## 5. System Architecture (High Level)

### Request Flow

```
User → Zunkiree Widget
     → Zunkiree API (FastAPI)
     → Vector DB (retrieve context)
     → LLM (answer generation)
     → Response validation
     → Widget displays answer
```

### Data Ingestion Flow

```
Customer Data (Website / PDFs)
     → Ingestion Service
     → Chunking
     → Embeddings
     → Vector DB
     → Metadata stored in Postgres
```

### Multi-Tenancy (v1)

- One logical tenant per customer
- Separate vector namespaces
- Shared infrastructure
- Config isolated per customer

---

## 6. System Design (Detailed)

### Backend Services

#### Ingestion Service

- Crawl selected URLs
- Upload PDFs / text
- Chunk + embed
- Store vectors

#### Query Service

- Receive question
- Retrieve relevant chunks
- Build grounded prompt
- Call LLM
- Validate response

#### Admin Service

- Upload data
- Trigger re-index
- Update config

### Prompt Design (Important)

System prompt must:

- Restrict answers to provided data
- Avoid hallucination
- Return "unknown" when needed
- Tone configurable per customer

---

## 7. Frontend Widget Design

### UI Requirements

- Small, clean widget
- Floating button or embedded container
- No emojis
- No AI "personality"
- Brand-adaptable colors
- Keyboard accessible

### Embed Method

```html
<script src="https://cdn.zunkiree.ai/search.js"
        data-site-id="SITE_ID"></script>
```

### Widget Behavior

- Open / close
- Send query
- Show loading state
- Render answer
- Optional follow-ups

---

## 8. Pilot Customer Setup

### Admizz Education

| Attribute | Value |
|-----------|-------|
| **Data** | Country pages, FAQs, process docs |
| **Tone** | Professional, advisory |
| **Goal** | Reduce counsellor load |

### Khems Cleaning

| Attribute | Value |
|-----------|-------|
| **Data** | Services, pricing, coverage |
| **Tone** | Simple, friendly |
| **Goal** | Guide users to services |

### Guntabya (OTA)

| Attribute | Value |
|-----------|-------|
| **Data** | Listings, policies, destination info |
| **Tone** | Neutral, informative |
| **Goal** | Improve discovery & confidence |

> **Same system. Different data.**

---

## 9. Task Breakdown (Build Order)

### Phase 1 — Core Backend

- [ ] Setup FastAPI project
- [ ] Database schema (customers, domains, configs)
- [ ] Ingestion pipeline
- [ ] Vector storage
- [ ] Query endpoint
- [ ] Prompt orchestration

### Phase 2 — Widget

- [ ] Widget UI
- [ ] Embed script
- [ ] API integration
- [ ] Theme support

### Phase 3 — Admin (Internal)

- [ ] Upload docs
- [ ] Trigger re-index
- [ ] Config editor

### Phase 4 — Pilot Integration

- [ ] Deploy per customer
- [ ] Test queries
- [ ] Fix edge cases

---

## 10. Security & Safety (v1)

- Domain allowlist per customer
- API key per site
- No PII storage
- No user tracking
- Rate limiting via Cloudflare

---

## 11. Guardrails (Read Carefully)

### Claude Code Must Not:

- Add features beyond scope
- Build dashboards
- Add pricing
- Optimize prematurely
- Over-abstract

### Claude Code Must:

- Keep code readable
- Keep services modular
- Favor clarity over cleverness
- Assume future scale but not build for it now

---

## 12. Success Criteria (v1)

Zunkiree Search v1 is successful if:

- It answers real questions accurately
- Pilot customers actively use it
- Users ask multiple questions per session
- Customers say: "This feels like part of our product"

---

## 13. Future (Out of Scope)

- Analytics
- Industry packs
- Multilingual
- APIs
- Self-serve onboarding
