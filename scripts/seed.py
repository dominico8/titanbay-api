"""Seed script placeholder.

Run with: ``uv run python -m scripts.seed``
"""
from __future__ import annotations

import asyncio
import logging

from app.database import AsyncSessionLocal

logger = logging.getLogger(__name__)


async def seed() -> None:
    async with AsyncSessionLocal() as session:  # noqa: F841 - placeholder
        logger.info("Seed script is a placeholder; no data inserted.")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(seed())
