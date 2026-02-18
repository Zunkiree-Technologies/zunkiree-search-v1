from __future__ import annotations

import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException, Header, UploadFile, File
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Customer, WidgetConfig, IngestionJob, DocumentChunk
from app.services.auth import verify_password, create_access_token, decode_access_token
from app.services.ingestion import get_ingestion_service
from app.utils.extractors import SUPPORTED_EXTENSIONS, SIZE_LIMITS, validate_file, get_file_category
from app.config import get_settings

router = APIRouter(prefix="/client", tags=["client"])
settings = get_settings()


# --- Auth dependency ---

async def get_current_customer(
    authorization: str = Header(...),
    db: AsyncSession = Depends(get_db),
) -> Customer:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    token = authorization[7:]
    try:
        payload = decode_access_token(token)
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid or expired token")

    customer_id = payload.get("sub")
    if not customer_id:
        raise HTTPException(status_code=401, detail="Invalid token payload")

    result = await db.execute(
        select(Customer).where(Customer.id == uuid.UUID(customer_id))
    )
    customer = result.scalar_one_or_none()

    if not customer or not customer.is_active:
        raise HTTPException(status_code=401, detail="Customer not found or inactive")

    return customer


# --- Request/Response models ---

class LoginRequest(BaseModel):
    email: str
    password: str


class LoginResponse(BaseModel):
    token: str
    customer: dict


class ProfileResponse(BaseModel):
    id: str
    name: str
    site_id: str
    email: str | None
    created_at: str


class ClientIngestUrlRequest(BaseModel):
    url: str = Field(..., description="URL to crawl")
    depth: int = Field(0, ge=0, le=2, description="Crawl depth")
    max_pages: int = Field(1, ge=1, le=50, description="Maximum pages to crawl")


class ClientIngestTextRequest(BaseModel):
    text: str = Field(..., min_length=10, description="Text content to ingest")
    title: str = Field("Uploaded Content", description="Title for the content")


class JobResponse(BaseModel):
    job_id: str
    status: str
    message: str


class JobInfo(BaseModel):
    id: str
    source_type: str
    source_url: str | None
    source_filename: str | None
    status: str
    chunks_created: int
    created_at: str
    completed_at: str | None


class JobsListResponse(BaseModel):
    jobs: list[JobInfo]
    total: int


class UpdateConfigRequest(BaseModel):
    brand_name: str | None = None
    tone: str | None = Field(None, pattern="^(formal|neutral|friendly)$")
    primary_color: str | None = Field(None, pattern="^#[0-9a-fA-F]{6}$")
    placeholder_text: str | None = None
    welcome_message: str | None = None
    fallback_message: str | None = None
    show_sources: bool | None = None
    show_suggestions: bool | None = None


class ConfigResponse(BaseModel):
    brand_name: str | None
    tone: str | None
    primary_color: str | None
    placeholder_text: str | None
    welcome_message: str | None
    fallback_message: str | None
    show_sources: bool | None
    show_suggestions: bool | None


class ApiKeyResponse(BaseModel):
    api_key_masked: str
    has_openai_key: bool
    openai_key_masked: str | None


class UpdateOpenAIKeyRequest(BaseModel):
    openai_api_key: str = Field(..., min_length=10)


class RegenerateApiKeyResponse(BaseModel):
    api_key: str
    message: str


# --- Endpoints ---

@router.post("/login", response_model=LoginResponse)
async def login(
    request: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    """Customer login with email and password."""
    result = await db.execute(
        select(Customer).where(Customer.email == request.email)
    )
    customer = result.scalar_one_or_none()

    if not customer or not customer.password_hash:
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not verify_password(request.password, customer.password_hash):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    if not customer.is_active:
        raise HTTPException(status_code=401, detail="Account is inactive")

    token = create_access_token(str(customer.id), customer.site_id)

    return LoginResponse(
        token=token,
        customer={
            "id": str(customer.id),
            "name": customer.name,
            "site_id": customer.site_id,
            "email": customer.email,
        },
    )


@router.get("/me", response_model=ProfileResponse)
async def get_profile(
    customer: Customer = Depends(get_current_customer),
):
    """Get current customer profile."""
    return ProfileResponse(
        id=str(customer.id),
        name=customer.name,
        site_id=customer.site_id,
        email=customer.email,
        created_at=customer.created_at.isoformat(),
    )


@router.get("/api-keys", response_model=ApiKeyResponse)
async def get_api_keys(
    customer: Customer = Depends(get_current_customer),
):
    """Get masked API keys for the current customer."""
    key = customer.api_key
    masked = key[:7] + "..." + key[-4:] if len(key) > 11 else key[:4] + "..."

    openai_masked = None
    if customer.openai_api_key:
        ok = customer.openai_api_key
        openai_masked = ok[:7] + "..." + ok[-4:] if len(ok) > 11 else ok[:4] + "..."

    return ApiKeyResponse(
        api_key_masked=masked,
        has_openai_key=customer.openai_api_key is not None,
        openai_key_masked=openai_masked,
    )


@router.put("/api-keys/openai")
async def update_openai_key(
    request: UpdateOpenAIKeyRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Save or update customer's OpenAI API key."""
    customer.openai_api_key = request.openai_api_key
    await db.commit()
    return {"message": "OpenAI API key saved successfully"}


@router.delete("/api-keys/openai")
async def delete_openai_key(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Remove customer's OpenAI API key (reverts to platform key)."""
    customer.openai_api_key = None
    await db.commit()
    return {"message": "OpenAI API key removed. Platform key will be used."}


@router.post("/api-keys/regenerate", response_model=RegenerateApiKeyResponse)
async def regenerate_api_key(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Regenerate the client API key. The full key is returned once."""
    new_key = f"zk_live_{secrets.token_hex(24)}"
    customer.api_key = new_key
    await db.commit()
    return RegenerateApiKeyResponse(
        api_key=new_key,
        message="API key regenerated. Copy it now — it won't be shown again.",
    )


@router.post("/ingest/url", response_model=JobResponse)
async def ingest_url(
    request: ClientIngestUrlRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Ingest content from a URL (scoped to current customer)."""
    ingestion_service = get_ingestion_service()

    try:
        job = await ingestion_service.ingest_url(
            db=db,
            customer_id=customer.id,
            site_id=customer.site_id,
            url=request.url,
            depth=request.depth,
            max_pages=request.max_pages,
        )

        return JobResponse(
            job_id=str(job.id),
            status=job.status,
            message=f"Ingestion completed. {job.chunks_created} chunks created.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INGESTION_FAILED", "message": str(e)},
        )


@router.post("/ingest/text", response_model=JobResponse)
async def ingest_text(
    request: ClientIngestTextRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Ingest raw text content (scoped to current customer)."""
    ingestion_service = get_ingestion_service()

    try:
        job = await ingestion_service.ingest_text(
            db=db,
            customer_id=customer.id,
            site_id=customer.site_id,
            text=request.text,
            source_title=request.title,
        )

        return JobResponse(
            job_id=str(job.id),
            status=job.status,
            message=f"Ingestion completed. {job.chunks_created} chunks created.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INGESTION_FAILED", "message": str(e)},
        )


@router.post("/ingest/file", response_model=JobResponse)
async def ingest_file(
    file: UploadFile = File(...),
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Ingest content from an uploaded file (PDF, Word, Excel, images, audio, video)."""
    if not file.filename:
        raise HTTPException(status_code=400, detail="No filename provided")

    # Read file content
    file_content = await file.read()

    # Validate file type and size
    is_valid, error_msg = validate_file(file.filename, len(file_content))
    if not is_valid:
        raise HTTPException(status_code=400, detail=error_msg)

    ingestion_service = get_ingestion_service()

    try:
        job = await ingestion_service.ingest_file(
            db=db,
            customer_id=customer.id,
            site_id=customer.site_id,
            file_content=file_content,
            filename=file.filename,
            openai_api_key=customer.openai_api_key,
        )

        return JobResponse(
            job_id=str(job.id),
            status=job.status,
            message=f"Ingestion completed. {job.chunks_created} chunks created.",
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail={"code": "INGESTION_FAILED", "message": str(e)},
        )


@router.get("/ingest/supported-types")
async def get_supported_types():
    """Return supported file extensions grouped by category."""
    categories: dict[str, list[str]] = {}
    for ext, category in SUPPORTED_EXTENSIONS.items():
        categories.setdefault(category, []).append(ext)

    return {
        "categories": categories,
        "size_limits": {k: v // (1024 * 1024) for k, v in SIZE_LIMITS.items()},
    }


@router.get("/jobs", response_model=JobsListResponse)
async def list_jobs(
    status: str | None = None,
    limit: int = 20,
    offset: int = 0,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """List ingestion jobs for the current customer."""
    query = select(IngestionJob).where(IngestionJob.customer_id == customer.id)

    if status:
        query = query.where(IngestionJob.status == status)

    query = query.order_by(IngestionJob.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    jobs = result.scalars().all()

    return JobsListResponse(
        jobs=[
            JobInfo(
                id=str(job.id),
                source_type=job.source_type,
                source_url=job.source_url,
                source_filename=job.source_filename,
                status=job.status,
                chunks_created=job.chunks_created,
                created_at=job.created_at.isoformat(),
                completed_at=job.completed_at.isoformat() if job.completed_at else None,
            )
            for job in jobs
        ],
        total=len(jobs),
    )


@router.get("/config", response_model=ConfigResponse)
async def get_config(
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Get widget configuration for the current customer."""
    result = await db.execute(
        select(WidgetConfig).where(WidgetConfig.customer_id == customer.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        return ConfigResponse(
            brand_name=customer.name,
            tone="neutral",
            primary_color="#2563eb",
            placeholder_text=None,
            welcome_message=None,
            fallback_message=None,
            show_sources=True,
            show_suggestions=True,
        )

    return ConfigResponse(
        brand_name=config.brand_name,
        tone=config.tone,
        primary_color=config.primary_color,
        placeholder_text=config.placeholder_text,
        welcome_message=config.welcome_message,
        fallback_message=config.fallback_message,
        show_sources=config.show_sources,
        show_suggestions=config.show_suggestions,
    )


@router.put("/config", response_model=ConfigResponse)
async def update_config(
    request: UpdateConfigRequest,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """Update widget configuration for the current customer."""
    result = await db.execute(
        select(WidgetConfig).where(WidgetConfig.customer_id == customer.id)
    )
    config = result.scalar_one_or_none()

    if not config:
        config = WidgetConfig(
            customer_id=customer.id,
            brand_name=customer.name,
        )
        db.add(config)

    update_data = request.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if value is not None:
            setattr(config, field, value)

    await db.commit()
    await db.refresh(config)

    return ConfigResponse(
        brand_name=config.brand_name,
        tone=config.tone,
        primary_color=config.primary_color,
        placeholder_text=config.placeholder_text,
        welcome_message=config.welcome_message,
        fallback_message=config.fallback_message,
        show_sources=config.show_sources,
        show_suggestions=config.show_suggestions,
    )


@router.get("/knowledge")
async def list_knowledge(
    search: str | None = None,
    limit: int = 50,
    offset: int = 0,
    customer: Customer = Depends(get_current_customer),
    db: AsyncSession = Depends(get_db),
):
    """List document chunks in the knowledge base for the current customer."""
    query = select(DocumentChunk).where(DocumentChunk.customer_id == customer.id)

    if search:
        query = query.where(
            DocumentChunk.content_preview.ilike(f"%{search}%")
            | DocumentChunk.source_title.ilike(f"%{search}%")
        )

    # Get total count
    from sqlalchemy import func
    count_query = select(func.count()).select_from(
        query.subquery()
    )
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    query = query.order_by(DocumentChunk.created_at.desc())
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    chunks = result.scalars().all()

    return {
        "chunks": [
            {
                "id": str(chunk.id),
                "source_title": chunk.source_title,
                "source_url": chunk.source_url,
                "content_preview": chunk.content_preview,
                "chunk_index": chunk.chunk_index,
                "token_count": chunk.token_count,
                "created_at": chunk.created_at.isoformat(),
            }
            for chunk in chunks
        ],
        "total": total,
    }


@router.get("/embed-code")
async def get_embed_code(
    customer: Customer = Depends(get_current_customer),
):
    """Get the embed code snippet for the current customer."""
    snippet = (
        f'<script\n'
        f'  src="https://zunkiree-search-v1.vercel.app/zunkiree-widget.iife.js"\n'
        f'  data-site-id="{customer.site_id}"\n'
        f'  data-api-url="https://api.zunkireelabs.com"\n'
        f'></script>'
    )
    return {"embed_code": snippet, "site_id": customer.site_id}
