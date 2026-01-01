import os
import random
from datetime import datetime, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
from faker import Faker

fake = Faker()
Faker.seed(42)
random.seed(42)
np.random.seed(42)

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

START_DATE = datetime(2024, 7, 1)
END_DATE = datetime(2025, 12, 31)
MONTHS = pd.date_range(START_DATE, END_DATE, freq='MS')

SEGMENTS = ['Enterprise', 'Mid-Market', 'SMB']
REGIONS = ['North America', 'EMEA', 'APAC', 'LATAM']
MARKETING_CHANNELS = ['Google Ads', 'LinkedIn', 'Content Marketing', 'Events', 'Referral']
ACQUISITION_CHANNELS = MARKETING_CHANNELS  # Must match marketing channels for CAC calculation
PLAN_TIERS = ['Starter', 'Professional', 'Business', 'Enterprise']
SUPPORT_CATEGORIES = ['Technical', 'Billing', 'Feature Request', 'Bug Report']
SEVERITIES = ['Low', 'Medium', 'High', 'Critical']

NUM_ACCOUNTS = 500
AVG_USERS_PER_ACCOUNT = 8


def generate_accounts():
    """Generate B2B customer accounts with realistic distribution."""
    accounts = []
    
    for i in range(NUM_ACCOUNTS):
        segment = np.random.choice(SEGMENTS, p=[0.15, 0.35, 0.50])
        
        created_date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
        
        # Seasonality: more signups in Q4
        month = created_date.month
        if month in [10, 11, 12]:
            created_date = created_date - timedelta(days=random.randint(0, 60))
        
        accounts.append({
            'account_id': f'ACC{i+1:05d}',
            'account_name': fake.company(),
            'segment': segment,
            'company_size': np.random.choice(['1-50', '51-200', '201-1000', '1000+'], 
                                            p=[0.4, 0.3, 0.2, 0.1]),
            'region': np.random.choice(REGIONS),
            'acquisition_channel': np.random.choice(ACQUISITION_CHANNELS),
            'created_at': created_date,
            'status': 'Active'
        })
    
    return pd.DataFrame(accounts)


def generate_users(accounts_df):
    """Generate users associated with accounts."""
    users = []
    user_id = 1
    
    for _, account in accounts_df.iterrows():
        num_users = max(1, int(np.random.poisson(AVG_USERS_PER_ACCOUNT)))
        
        for _ in range(num_users):
            users.append({
                'user_id': f'USR{user_id:06d}',
                'account_id': account['account_id'],
                'email': fake.email(),
                'role': np.random.choice(['Admin', 'User', 'Viewer'], p=[0.2, 0.6, 0.2]),
                'created_at': account['created_at'] + timedelta(days=random.randint(0, 30))
            })
            user_id += 1
    
    return pd.DataFrame(users)


def generate_subscriptions(accounts_df):
    """Generate subscriptions with churn behavior."""
    subscriptions = []
    sub_id = 1
    
    for _, account in accounts_df.iterrows():
        start_date = account['created_at']
        
        tier = PLAN_TIERS[SEGMENTS.index(account['segment'])] if account['segment'] == 'Enterprise' else \
               np.random.choice(PLAN_TIERS, p=[0.3, 0.4, 0.2, 0.1])
        
        # Churn logic will be applied based on usage
        end_date = None
        if random.random() < 0.15:  # 15% churn rate
            end_date = start_date + timedelta(days=random.randint(90, 400))
            if end_date > END_DATE:
                end_date = None
        
        subscriptions.append({
            'subscription_id': f'SUB{sub_id:05d}',
            'account_id': account['account_id'],
            'plan_tier': tier,
            'start_date': start_date,
            'end_date': end_date,
            'status': 'Cancelled' if end_date else 'Active'
        })
        sub_id += 1
    
    return pd.DataFrame(subscriptions)


def generate_invoices_payments(subscriptions_df):
    """Generate monthly invoices and payments for MRR calculation."""
    invoices = []
    payments = []
    invoice_id = 1
    payment_id = 1
    
    plan_mrr = {
        'Starter': 99,
        'Professional': 299,
        'Business': 799,
        'Enterprise': 2499
    }
    
    for _, sub in subscriptions_df.iterrows():
        start = sub['start_date']
        end = sub['end_date'] if pd.notna(sub['end_date']) else END_DATE
        
        # Generate monthly invoices
        for invoice_date in pd.date_range(start, end, freq='MS'):
            mrr = plan_mrr[sub['plan_tier']]
            
            # Revenue expansion for high-usage accounts (simulated)
            if random.random() < 0.05:
                mrr *= 1.2
            
            invoices.append({
                'invoice_id': f'INV{invoice_id:06d}',
                'subscription_id': sub['subscription_id'],
                'account_id': sub['account_id'],
                'invoice_date': invoice_date,
                'amount': round(mrr, 2),
                'status': 'Paid'
            })
            
            # Generate payment
            payments.append({
                'payment_id': f'PAY{payment_id:06d}',
                'invoice_id': f'INV{invoice_id:06d}',
                'payment_date': invoice_date + timedelta(days=random.randint(1, 10)),
                'amount': round(mrr, 2),
                'payment_method': np.random.choice(['Credit Card', 'ACH', 'Wire Transfer'])
            })
            
            invoice_id += 1
            payment_id += 1
    
    return pd.DataFrame(invoices), pd.DataFrame(payments)


def generate_crm_deals(accounts_df):
    """Generate pipeline deals with conversion rates by segment."""
    deals = []
    deal_id = 1
    
    stages = ['Lead', 'MQL', 'SQL', 'Proposal', 'Negotiation', 'Closed Won', 'Closed Lost']
    
    for _, account in accounts_df.iterrows():
        # Create won deal for each account
        deal_value = {
            'Enterprise': random.randint(50000, 150000),
            'Mid-Market': random.randint(15000, 50000),
            'SMB': random.randint(3000, 15000)
        }[account['segment']]
        
        created_date = account['created_at'] - timedelta(days=random.randint(30, 120))
        
        deals.append({
            'deal_id': f'DEAL{deal_id:05d}',
            'account_id': account['account_id'],
            'deal_value': deal_value,
            'stage': 'Closed Won',
            'created_date': created_date,
            'closed_date': account['created_at'],
            'sales_cycle_days': (account['created_at'] - created_date).days,
            'segment': account['segment']
        })
        deal_id += 1
    
    # Generate lost deals
    num_lost = int(NUM_ACCOUNTS * 0.3)
    for i in range(num_lost):
        segment = np.random.choice(SEGMENTS, p=[0.15, 0.35, 0.50])
        created_date = START_DATE + timedelta(days=random.randint(0, (END_DATE - START_DATE).days))
        
        deals.append({
            'deal_id': f'DEAL{deal_id:05d}',
            'account_id': None,
            'deal_value': random.randint(5000, 100000),
            'stage': 'Closed Lost',
            'created_date': created_date,
            'closed_date': created_date + timedelta(days=random.randint(20, 90)),
            'sales_cycle_days': random.randint(20, 90),
            'segment': segment
        })
        deal_id += 1
    
    return pd.DataFrame(deals)


def generate_product_events(users_df, subscriptions_df):
    """Generate product usage events with activation patterns."""
    events = []
    event_id = 1
    
    event_types = ['login', 'feature_use', 'activation', 'weekly_active']
    
    for _, user in users_df.iterrows():
        user_start = user['created_at']
        
        # Activation event
        if random.random() < 0.85:  # 85% activation rate
            activation_date = user_start + timedelta(days=random.randint(1, 14))
            events.append({
                'event_id': f'EVT{event_id:08d}',
                'user_id': user['user_id'],
                'account_id': user['account_id'],
                'event_type': 'activation',
                'event_timestamp': activation_date
            })
            event_id += 1
            
            # Weekly active events
            for week_offset in range(0, (END_DATE - activation_date).days // 7):
                if random.random() < 0.7:  # 70% weekly active
                    events.append({
                        'event_id': f'EVT{event_id:08d}',
                        'user_id': user['user_id'],
                        'account_id': user['account_id'],
                        'event_type': 'weekly_active',
                        'event_timestamp': activation_date + timedelta(weeks=week_offset)
                    })
                    event_id += 1
    
    return pd.DataFrame(events)


def generate_support_tickets(accounts_df, product_events_df):
    """Generate support tickets with SLA and severity."""
    tickets = []
    ticket_id = 1
    
    for _, account in accounts_df.iterrows():
        # Ticket volume varies by account
        num_tickets = random.randint(1, 20)
        
        for _ in range(num_tickets):
            created_date = account['created_at'] + timedelta(days=random.randint(0, (END_DATE - account['created_at']).days))
            
            severity = np.random.choice(SEVERITIES, p=[0.5, 0.3, 0.15, 0.05])
            category = np.random.choice(SUPPORT_CATEGORIES)
            
            sla_hours = {'Low': 48, 'Medium': 24, 'High': 8, 'Critical': 2}[severity]
            resolution_hours = sla_hours * random.uniform(0.5, 1.5)
            
            tickets.append({
                'ticket_id': f'TKT{ticket_id:06d}',
                'account_id': account['account_id'],
                'category': category,
                'severity': severity,
                'created_at': created_date,
                'resolved_at': created_date + timedelta(hours=resolution_hours),
                'sla_hours': sla_hours,
                'resolution_hours': round(resolution_hours, 1),
                'sla_breached': resolution_hours > sla_hours
            })
            ticket_id += 1
    
    return pd.DataFrame(tickets)


def generate_marketing_spend(accounts_df):
    """Generate marketing spend with channel attribution."""
    spend_records = []
    
    for month in MONTHS:
        for channel in MARKETING_CHANNELS:
            # Spend varies by channel
            base_spend = {
                'Google Ads': 25000,
                'LinkedIn': 18000,
                'Content Marketing': 12000,
                'Events': 30000,
                'Referral': 5000
            }[channel]
            
            # Seasonal variation
            if month.month in [10, 11, 12]:
                base_spend *= 1.3
            
            monthly_spend = base_spend * random.uniform(0.8, 1.2)
            
            # Leads generated
            leads = int(monthly_spend / random.randint(80, 150))
            
            spend_records.append({
                'month': month,
                'channel': channel,
                'spend': round(monthly_spend, 2),
                'leads_generated': leads,
                'campaign_name': f'{channel} {month.strftime("%b %Y")}'
            })
    
    return pd.DataFrame(spend_records)


def main():
    print("Generating synthetic SaaS GTM data...")
    
    print("  → Accounts...")
    accounts = generate_accounts()
    
    print("  → Users...")
    users = generate_users(accounts)
    
    print("  → Subscriptions...")
    subscriptions = generate_subscriptions(accounts)
    
    print("  → Invoices & Payments...")
    invoices, payments = generate_invoices_payments(subscriptions)
    
    print("  → CRM Deals...")
    crm_deals = generate_crm_deals(accounts)
    
    print("  → Product Events...")
    product_events = generate_product_events(users, subscriptions)
    
    print("  → Support Tickets...")
    support_tickets = generate_support_tickets(accounts, product_events)
    
    print("  → Marketing Spend...")
    marketing_spend = generate_marketing_spend(accounts)
    
    # Save to CSV
    print("\nSaving data to CSV...")
    accounts.to_csv(OUTPUT_DIR / 'accounts.csv', index=False)
    users.to_csv(OUTPUT_DIR / 'users.csv', index=False)
    subscriptions.to_csv(OUTPUT_DIR / 'subscriptions.csv', index=False)
    invoices.to_csv(OUTPUT_DIR / 'invoices.csv', index=False)
    payments.to_csv(OUTPUT_DIR / 'payments.csv', index=False)
    crm_deals.to_csv(OUTPUT_DIR / 'crm_deals.csv', index=False)
    product_events.to_csv(OUTPUT_DIR / 'product_events.csv', index=False)
    support_tickets.to_csv(OUTPUT_DIR / 'support_tickets.csv', index=False)
    marketing_spend.to_csv(OUTPUT_DIR / 'marketing_spend.csv', index=False)
    
    print("\n✅ Data generation complete!")
    print(f"\nSummary:")
    print(f"  Accounts: {len(accounts):,}")
    print(f"  Users: {len(users):,}")
    print(f"  Subscriptions: {len(subscriptions):,}")
    print(f"  Invoices: {len(invoices):,}")
    print(f"  Payments: {len(payments):,}")
    print(f"  CRM Deals: {len(crm_deals):,}")
    print(f"  Product Events: {len(product_events):,}")
    print(f"  Support Tickets: {len(support_tickets):,}")
    print(f"  Marketing Spend Records: {len(marketing_spend):,}")


if __name__ == '__main__':
    main()
