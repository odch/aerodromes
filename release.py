#!/usr/bin/env python3
"""
Aerodrome Registry Release Tool

Promotes staging version to production after manual review and approval.
"""
import json
import shutil
import sys
from datetime import datetime
from pathlib import Path

def backup_production(prod_file: str = 'aerodromes.json') -> str:
    """Create backup of current production file."""
    if not Path(prod_file).exists():
        return ""
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"backups/aerodromes_backup_{timestamp}.json"
    
    # Create backups directory if it doesn't exist
    Path("backups").mkdir(exist_ok=True)
    
    shutil.copy2(prod_file, backup_file)
    return backup_file

def validate_staging(staging_file: str = 'aerodromes-staging.json') -> bool:
    """Validate staging file before promotion."""
    try:
        with open(staging_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Basic validation
        required_fields = ['version', 'last_updated', 'total_count', 'aerodromes']
        for field in required_fields:
            if field not in data:
                print(f"❌ Missing required field: {field}")
                return False
        
        if not isinstance(data['aerodromes'], list):
            print("❌ Aerodromes must be a list")
            return False
        
        if data['total_count'] != len(data['aerodromes']):
            print(f"❌ Count mismatch: total_count={data['total_count']}, actual={len(data['aerodromes'])}")
            return False
        
        # Sample aerodrome validation
        if data['aerodromes']:
            sample = data['aerodromes'][0]
            required_aerodrome_fields = ['icao', 'name', 'country', 'timezone']
            for field in required_aerodrome_fields:
                if field not in sample:
                    print(f"❌ Missing aerodrome field: {field}")
                    return False
        
        print(f"✅ Staging validation passed: {len(data['aerodromes'])} aerodromes")
        return True
        
    except FileNotFoundError:
        print(f"❌ Staging file not found: {staging_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in staging file: {e}")
        return False

def release_to_production(staging_file: str = 'aerodromes-staging.json',
                         prod_file: str = 'aerodromes.json',
                         force: bool = False) -> bool:
    """Release staging version to production."""
    print("🚀 Starting release process...")
    print(f"🚧 Staging: {staging_file}")
    print(f"📦 Production: {prod_file}")
    print("-" * 50)
    
    # Check if staging file exists
    if not Path(staging_file).exists():
        print(f"❌ Staging file not found: {staging_file}")
        print("💡 Run sync first to generate staging data")
        return False
    
    # Validate staging
    if not validate_staging(staging_file):
        print("❌ Staging validation failed")
        return False
    
    # Interactive confirmation unless forced
    if not force:
        print("⚠️  This will replace the current production registry.")
        print("📱 All downstream apps will use the new data on their next sync.")
        response = input("\n🤔 Proceed with release? (yes/no): ").strip().lower()
        
        if response not in ['yes', 'y']:
            print("❌ Release cancelled by user")
            return False
    
    try:
        # Create backup of current production
        backup_file = backup_production(prod_file)
        if backup_file:
            print(f"💾 Production backup created: {backup_file}")
        
        # Promote staging to production
        shutil.copy2(staging_file, prod_file)
        
        # Update production metadata
        with open(prod_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Add release timestamp
        data['released_at'] = datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z')
        
        with open(prod_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print("✅ Release completed successfully!")
        print(f"📊 Released {data['total_count']} aerodromes to production")
        print(f"🕐 Release timestamp: {data['released_at']}")
        
        # Show next steps
        print("\n💡 Next steps:")
        print("1. Commit changes to git repository")
        print("2. Monitor downstream apps for successful sync")
        print("3. Check logs for any issues")
        
        return True
        
    except Exception as e:
        print(f"❌ Release failed: {e}")
        return False

def rollback_production(backup_pattern: str = None) -> bool:
    """Rollback production to previous backup."""
    backups_dir = Path("backups")
    if not backups_dir.exists():
        print("❌ No backups directory found")
        return False
    
    # Find available backups
    backups = sorted(backups_dir.glob("aerodromes_backup_*.json"), reverse=True)
    if not backups:
        print("❌ No backup files found")
        return False
    
    print("📋 Available backups:")
    for i, backup in enumerate(backups[:5]):  # Show last 5 backups
        print(f"  {i+1}. {backup.name}")
    
    try:
        choice = input("\n🤔 Select backup to restore (1-5, or 'cancel'): ").strip()
        if choice.lower() == 'cancel':
            print("❌ Rollback cancelled")
            return False
        
        backup_index = int(choice) - 1
        if backup_index < 0 or backup_index >= len(backups[:5]):
            print("❌ Invalid selection")
            return False
        
        selected_backup = backups[backup_index]
        
        # Confirm rollback
        print(f"⚠️  This will replace production with: {selected_backup.name}")
        confirm = input("🤔 Confirm rollback? (yes/no): ").strip().lower()
        
        if confirm not in ['yes', 'y']:
            print("❌ Rollback cancelled")
            return False
        
        # Perform rollback
        shutil.copy2(selected_backup, 'aerodromes.json')
        print(f"✅ Rolled back to {selected_backup.name}")
        return True
        
    except (ValueError, IndexError):
        print("❌ Invalid input")
        return False
    except Exception as e:
        print(f"❌ Rollback failed: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "rollback":
        rollback_production()
    elif len(sys.argv) > 1 and sys.argv[1] == "--force":
        release_to_production(force=True)
    else:
        release_to_production()
