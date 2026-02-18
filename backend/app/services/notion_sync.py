from __future__ import annotations

import json
import uuid
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

import httpx

from app.models import IngestionJob, Connector
from app.services.ingestion import get_ingestion_service
from app.utils.chunking import chunk_text


NOTION_API_VERSION = "2022-06-28"
NOTION_BASE_URL = "https://api.notion.com/v1"


class NotionSyncService:
    """Sync Notion pages into the ingestion pipeline."""

    async def sync_connector(
        self,
        db: AsyncSession,
        connector: Connector,
        site_id: str,
    ) -> IngestionJob:
        """
        Sync all pages from a Notion workspace.

        1. Search for all pages via Notion Search API
        2. Extract block children as plain text
        3. Feed into the existing ingestion chunk pipeline
        4. Update connector.last_synced_at
        """
        creds = json.loads(connector.credentials)
        api_key = creds.get("api_key") or creds.get("access_token", "")
        if not api_key:
            raise ValueError("Notion API key not configured")

        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": NOTION_API_VERSION,
            "Content-Type": "application/json",
        }

        # Create ingestion job
        job = IngestionJob(
            customer_id=connector.customer_id,
            source_type="notion",
            source_filename=f"Notion Sync — {connector.display_name}",
            status="processing",
            started_at=datetime.utcnow(),
        )
        db.add(job)
        await db.commit()
        await db.refresh(job)

        try:
            # 1. Search for all pages
            pages = await self._search_pages(headers)

            # 2. Extract text from each page
            all_chunks = []
            for page in pages:
                page_id = page["id"]
                title = self._extract_page_title(page)

                try:
                    text = await self._get_page_text(headers, page_id)
                    if not text or len(text.strip()) < 10:
                        continue

                    chunks = chunk_text(text)
                    for chunk in chunks:
                        chunk["source_title"] = title
                        chunk["source_url"] = page.get("url", "")
                    all_chunks.extend(chunks)
                except Exception as e:
                    print(f"Error extracting Notion page {page_id}: {e}")
                    continue

            # 3. Process chunks through the ingestion pipeline
            if all_chunks:
                ingestion_service = get_ingestion_service()
                await ingestion_service._process_chunks(
                    db=db,
                    job=job,
                    site_id=site_id,
                    chunks=all_chunks,
                )

            job.status = "completed"
            job.chunks_created = len(all_chunks)
            job.completed_at = datetime.utcnow()

            # 4. Update connector sync timestamp
            connector.last_synced_at = datetime.utcnow()
            await db.commit()

        except Exception as e:
            job.status = "failed"
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()
            await db.commit()
            raise

        return job

    async def _search_pages(self, headers: dict) -> list[dict]:
        """Search Notion for all pages."""
        pages = []
        has_more = True
        start_cursor = None

        async with httpx.AsyncClient(timeout=30) as client:
            while has_more:
                body: dict = {"filter": {"value": "page", "property": "object"}, "page_size": 100}
                if start_cursor:
                    body["start_cursor"] = start_cursor

                resp = await client.post(
                    f"{NOTION_BASE_URL}/search",
                    headers=headers,
                    json=body,
                )
                resp.raise_for_status()
                data = resp.json()

                pages.extend(data.get("results", []))
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

        return pages

    async def _get_page_text(self, headers: dict, page_id: str) -> str:
        """Get all block children of a page as plain text."""
        blocks = []
        has_more = True
        start_cursor = None

        async with httpx.AsyncClient(timeout=30) as client:
            while has_more:
                url = f"{NOTION_BASE_URL}/blocks/{page_id}/children?page_size=100"
                if start_cursor:
                    url += f"&start_cursor={start_cursor}"

                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                data = resp.json()

                blocks.extend(data.get("results", []))
                has_more = data.get("has_more", False)
                start_cursor = data.get("next_cursor")

        return self._blocks_to_text(blocks)

    def _blocks_to_text(self, blocks: list[dict]) -> str:
        """Convert Notion blocks to plain text."""
        lines = []
        for block in blocks:
            block_type = block.get("type", "")
            block_data = block.get(block_type, {})

            # Extract rich_text from common block types
            rich_text = block_data.get("rich_text", [])
            text = "".join(t.get("plain_text", "") for t in rich_text)

            if block_type in ("heading_1", "heading_2", "heading_3"):
                lines.append(f"\n{text}\n")
            elif block_type in ("paragraph", "quote", "callout"):
                if text:
                    lines.append(text)
            elif block_type in ("bulleted_list_item", "numbered_list_item"):
                lines.append(f"- {text}")
            elif block_type == "to_do":
                checked = block_data.get("checked", False)
                lines.append(f"[{'x' if checked else ' '}] {text}")
            elif block_type == "code":
                lang = block_data.get("language", "")
                lines.append(f"```{lang}\n{text}\n```")
            elif block_type == "divider":
                lines.append("---")
            elif block_type == "toggle":
                if text:
                    lines.append(text)
            # Skip unsupported types silently

        return "\n".join(lines)

    def _extract_page_title(self, page: dict) -> str:
        """Extract title from a Notion page object."""
        props = page.get("properties", {})

        # Try common title property names
        for key in ("title", "Title", "Name", "name"):
            prop = props.get(key, {})
            if prop.get("type") == "title":
                title_parts = prop.get("title", [])
                return "".join(t.get("plain_text", "") for t in title_parts) or "Untitled"

        # Fallback: iterate all properties looking for type=title
        for prop in props.values():
            if isinstance(prop, dict) and prop.get("type") == "title":
                title_parts = prop.get("title", [])
                return "".join(t.get("plain_text", "") for t in title_parts) or "Untitled"

        return "Untitled"


# Singleton
_notion_sync_service: NotionSyncService | None = None


def get_notion_sync_service() -> NotionSyncService:
    global _notion_sync_service
    if _notion_sync_service is None:
        _notion_sync_service = NotionSyncService()
    return _notion_sync_service
