import asyncio
import logging
from datetime import UTC, datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.models import (
    SyncOutbox,
)

logger = logging.getLogger(__name__)


class SyncProcessor:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def process_outbox(self, batch_size: int = 50):
        """Process pending sync outbox entries."""
        result = await self.db.execute(
            select(SyncOutbox).where(
                SyncOutbox.status == "pending"
            ).order_by(SyncOutbox.created_at).limit(50)
        )
        entries = result.scalars().all()

        for entry in entries:
            await self.process_entry(entry)

    async def process_entry(self, entry: "SyncOutbox"):
        """Process a single sync outbox entry."""
        try:
            await self.db.execute(
                update(SyncOutbox)
                .where(SyncOutbox.id == entry.id)
                .values(status="processing", attempts=SyncOutbox.attempts + 1)
            )
            await self.db.commit()

            # Process based on table and operation
            if entry.table_name == "messages":
                await self._process_message(entry)
            elif entry.table_name == "applications":
                await self._process_application(entry)
            elif entry.table_name == "notifications":
                await self._process_notification(entry)
            elif entry.table_name == "chats":
                await self._process_chat(entry)
            else:
                logger.warning(f"Unknown table: {entry.table_name}")

            # Mark as completed
            await self.db.execute(
                update(SyncOutbox)
                .where(SyncOutbox.id == entry.id)
                .values(status="completed", processed_at=datetime.now(UTC))
            )
            await self.db.commit()

        except Exception as e:
            logger.error(f"Sync processing failed for {entry.id}: {e}")
            await self.db.execute(
                update(SyncOutbox)
                .where(SyncOutbox.id == entry.id)
                .values(
                    status="failed",
                    last_error=str(e),
                    attempts=SyncOutbox.attempts + 1
                )
            )
            await self.db.commit()

    async def _process_message(self, entry: "SyncOutbox"):
        payload = entry.payload
        operation = entry.operation

        if operation == "INSERT":
            # Message already created locally, just confirm
            pass
        elif operation == "UPDATE":
            # Update message status, etc.
            pass
        elif operation == "DELETE":
            # Soft delete
            pass

    async def _process_application(self, entry: "SyncOutbox"):
        payload = entry.payload
        operation = entry.operation

        if operation == "INSERT":
            pass

    async def _process_notification(self, entry: "SyncOutbox"):
        pass

    async def _process_chat(self, entry: "SyncOutbox"):
        pass


async def process_sync_queue():
    """Background worker to process sync outbox."""
    while True:
        try:
            async with AsyncSessionLocal() as db:
                processor = SyncProcessor(db)
                await processor.process_outbox()
        except Exception as e:
            logging.error(f"Sync processor error: {e}")

        await asyncio.sleep(5)  # Process every 5 seconds


async def main():
    await process_sync_queue()


if __name__ == "__main__":
    asyncio.run(main())
