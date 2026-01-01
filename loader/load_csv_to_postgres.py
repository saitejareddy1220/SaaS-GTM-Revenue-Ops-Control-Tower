import os
import sys
import time
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv(Path(__file__).parent.parent / '.env')

DB_HOST = os.getenv('POSTGRES_HOST', 'localhost')
DB_PORT = os.getenv('POSTGRES_PORT', '5432')
DB_NAME = os.getenv('POSTGRES_DB', 'saas_analytics')
DB_USER = os.getenv('POSTGRES_USER', 'analytics_user')
DB_PASSWORD = os.getenv('POSTGRES_PASSWORD', 'analytics_pass')

DATA_DIR = Path(__file__).parent.parent / 'data_gen' / 'output'

DATABASE_URL = f'postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}'


def wait_for_db(engine, max_retries=10):
    """Wait for database to be ready."""
    for i in range(max_retries):
        try:
            with engine.connect() as conn:
                conn.execute(text('SELECT 1'))
            print("✅ Database connection successful")
            return True
        except Exception as e:
            print(f"⏳ Waiting for database... ({i+1}/{max_retries})")
            time.sleep(3)
    
    print("❌ Failed to connect to database")
    return False


def load_csv_to_table(engine, csv_path, table_name):
    """Load CSV data into Postgres table."""
    print(f"  Loading {csv_path.name} → {table_name}...")
    
    df = pd.read_csv(csv_path)
    
    df.to_sql(
        table_name,
        engine,
        if_exists='replace',
        index=False,
        method='multi'
    )
    
    print(f"    ✓ Loaded {len(df):,} rows")
    return len(df)


def main():
    print("Loading data into Postgres warehouse...")
    print(f"Connection: {DB_HOST}:{DB_PORT}/{DB_NAME}\n")
    
    engine = create_engine(DATABASE_URL)
    
    if not wait_for_db(engine):
        sys.exit(1)
    
    datasets = [
        ('accounts.csv', 'raw_accounts'),
        ('users.csv', 'raw_users'),
        ('subscriptions.csv', 'raw_subscriptions'),
        ('invoices.csv', 'raw_invoices'),
        ('payments.csv', 'raw_payments'),
        ('crm_deals.csv', 'raw_crm_deals'),
        ('product_events.csv', 'raw_product_events'),
        ('support_tickets.csv', 'raw_support_tickets'),
        ('marketing_spend.csv', 'raw_marketing_spend')
    ]
    
    total_rows = 0
    
    for csv_file, table_name in datasets:
        csv_path = DATA_DIR / csv_file
        
        if not csv_path.exists():
            print(f"⚠️  {csv_file} not found, skipping...")
            continue
        
        rows = load_csv_to_table(engine, csv_path, table_name)
        total_rows += rows
    
    print(f"\n✅ Data loading complete! Total rows: {total_rows:,}")


if __name__ == '__main__':
    main()
