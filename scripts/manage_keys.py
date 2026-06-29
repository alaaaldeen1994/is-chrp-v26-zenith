import os
import sys
import hashlib
import secrets
import argparse
from datetime import datetime, timedelta

# Adjust path to import from workspace root
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.connection import Base, engine, SessionLocal
from database.models import APIKey

def init_db():
    print("Initializing database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")

def generate_key(owner: str, tier: str, expires_in_days: int = None) -> str:
    # 1. Create a secure random token
    raw_token = secrets.token_hex(16)  # 32 characters
    api_key = f"zk_live_{raw_token}"
    
    # 2. Hash and prepare prefix
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    prefix = f"zk_live_{raw_token[:4]}...{raw_token[-4:]}"
    
    # 3. Expiry date calculation
    expires_at = None
    if expires_in_days:
        expires_at = datetime.utcnow() + timedelta(days=expires_in_days)
        
    db = SessionLocal()
    try:
        db_key = APIKey(
            key_hash=key_hash,
            prefix=prefix,
            owner=owner,
            tier=tier.lower(),
            is_active=True,
            expires_at=expires_at
        )
        db.add(db_key)
        db.commit()
        
        print("\n" + "="*60)
        print("API KEY CREATED SUCCESSFULLY")
        print("="*60)
        print(f"Owner:       {owner}")
        print(f"Tier:        {tier.upper()}")
        print(f"Expires At:  {expires_at if expires_at else 'Never'}")
        print(f"Plain Key:   {api_key}")
        print("="*60)
        print("WARNING: Copy the key now. It is hashed in the database and cannot be recovered.\n")
    finally:
        db.close()

def list_keys():
    db = SessionLocal()
    try:
        keys = db.query(APIKey).all()
        if not keys:
            print("No API keys found in database.")
            return
            
        print("\n" + "="*80)
        print(f"{'ID':<4} | {'Prefix':<18} | {'Owner':<20} | {'Tier':<12} | {'Active':<6} | {'Created At':<19}")
        print("="*80)
        for key in keys:
            print(f"{key.id:<4} | {key.prefix:<18} | {key.owner:<20} | {key.tier.upper():<12} | {str(key.is_active):<6} | {key.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print("="*80 + "\n")
    finally:
        db.close()

def revoke_key(key_id: int):
    db = SessionLocal()
    try:
        key = db.query(APIKey).filter(APIKey.id == key_id).first()
        if not key:
            print(f"API Key with ID {key_id} not found.")
            return
            
        key.is_active = False
        db.commit()
        print(f"API Key with ID {key_id} ({key.prefix}) has been revoked.")
    finally:
        db.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Zenith API Key Lifecycle Manager")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Init DB Command
    subparsers.add_parser("init-db", help="Initialize database tables")
    
    # Create key command
    create_parser = subparsers.add_parser("create", help="Create a new API Key")
    create_parser.add_argument("--owner", required=True, help="Name of client/organization")
    create_parser.add_argument("--tier", default="free", choices=["free", "professional", "enterprise"], help="Access tier")
    create_parser.add_argument("--expires", type=int, default=None, help="Expiry time in days")
    
    # List keys command
    subparsers.add_parser("list", help="List all API Keys")
    
    # Revoke key command
    revoke_parser = subparsers.add_parser("revoke", help="Revoke an API Key")
    revoke_parser.add_argument("--id", type=int, required=True, help="ID of the API key to revoke")
    
    args = parser.parse_args()
    
    # Auto-initialize DB tables on any command if they don't exist
    init_db()
    
    if args.command == "create":
        generate_key(args.owner, args.tier, args.expires)
    elif args.command == "list":
        list_keys()
    elif args.command == "revoke":
        revoke_key(args.id)
    elif args.command == "init-db":
        pass  # init_db is called automatically above
    else:
        parser.print_help()
