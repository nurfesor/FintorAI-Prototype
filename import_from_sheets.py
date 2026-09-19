import asyncio
import logging
from datetime import datetime

from config import config
from database import SessionLocal, TransactionDB, init_db
from services.google_sheets import SheetsService

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def parse_date(date_str: str) -> datetime | None:
    formats_to_try = ['%Y-%m-%dT%H:%M:%S', '%d.%m.%Y', '%Y-%m-%d']
    for fmt in formats_to_try:
        try:
            return datetime.strptime(date_str, fmt)
        except (ValueError, TypeError):
            continue
    logging.warning(f"Could not parse date: {date_str}")
    return None

def parse_amount(amount_str: str) -> float | None:
    try:
        return float(str(amount_str).replace(',', '.').replace(' ', ''))
    except (ValueError, TypeError):
        logging.warning(f"Could not parse amount: {amount_str}")
        return None

async def run_migration():
    print("--- Starting Data Migration ---")
    
    print("Step 1: Initializing local database...")
    init_db()
    print("Database initialized.")

    print("\nStep 2: Connecting to Google Sheets...")
    sheets = SheetsService(str(config.google_credentials_json), config.spreadsheet_id)
    print("Connection successful.")

    print("\nStep 3: Fetching all operations from the sheet...")
    all_rows = await sheets.get_all_operations()
    
    if not all_rows:
        print("No operations found in Google Sheet. Exiting.")
        return

    print(f"Found {len(all_rows)} transactions to import.")

    print("\nStep 4: Processing and importing transactions...")
    db = SessionLocal()
    try:
        imported_count, skipped_count = 0, 0
        for i, row in enumerate(all_rows):
            print(f"  Processing row {i+1}/{len(all_rows)}...", end='\r')
            
            if len(row) < 6:
                skipped_count += 1
                continue
            
            date_val, amount_val = parse_date(row[0]), parse_amount(row[4])
            if not date_val or amount_val is None:
                skipped_count += 1
                continue

            db.add(TransactionDB(
                user_id=0, transaction_date=date_val, category=row[1],
                group=row[2], subcategory=row[3], amount=amount_val,
                description=row[5]
            ))
            imported_count += 1

        print("\nCommitting changes to the database...")
        db.commit()
        print("\n--- Migration Complete! ---")
        print(f"✅ Successfully imported: {imported_count} transactions.")
        if skipped_count > 0:
            print(f"⚠️ Skipped: {skipped_count} rows due to formatting issues.")

    except Exception as e:
        print(f"\nAn error occurred during migration: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    asyncio.run(run_migration())
