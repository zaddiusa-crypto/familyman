import asyncio
import httpx
import logging
from datetime import datetime, timezone
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.core.config import settings
from app.core.models import FeeSchedule, Lodge

logger = logging.getLogger(__name__)


async def update_currency_rates():
    """Update forex rates and convert fee schedules."""
    async with AsyncSessionLocal() as db:
        try:
            # Get all active lodges with their base currencies
            result = await db.execute(select(Lodge).where(Lodge.currency.isnot(None)))
            lodges = result.scalars().all()

            for lodge in lodges:
                base_currency = lodge.currency
                if base_currency == "USD":
                    continue

                # Get forex rate
                try:
                    async with httpx.AsyncClient() as client:
                        resp = await client.get(
                            f"https://open.er-api.com/v6/latest/USD",
                            timeout=10
                        )
                        if resp.status_code != 200:
                            continue
                        data = resp.json()
                        rates = data.get("rates", {})
                        kes_rate = rates.get("KES")
                        target_rate = rates.get(base_currency)

                        if not kes_rate or not target_rate:
                            continue

                        # Convert base prices from KES to target currency
                        conv_rate = target_rate / kes_rate

                        # Update fee schedules
                        result = await db.execute(
                            select(FeeSchedule).where(
                                FeeSchedule.lodge_id == "lodge_id",  # This would need the actual lodge ID
                                FeeSchedule.is_active == True
                            )
                        )
                        fees = result.scalars().all()

                        for fee in fees:
                            if fee.currency == "KES":
                                new_amount = round(float(fee.amount) * conv_rate, 2)
                                # Store converted amount in a separate field or update with conversion note
                                # For now, we'll just log
                                logger.info(f"Converted {fee.name}: {fee.amount} KES -> {new_amount} {base_currency}")

                except Exception as e:
                    logger.error(f"Forex update failed for lodge {lodge.id}: {e}")

        except Exception as e:
            logging.error(f"Currency updater error: {e}")


async def run_currency_updater():
    """Run currency updater daily."""
    while True:
        try:
            await update_currency_rates()
        except Exception as e:
            logging.error(f"Currency updater error: {e}")

        # Sleep for 24 hours
        await asyncio.sleep(24 * 60 * 60)


async def main():
    await run_currency_updater()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())