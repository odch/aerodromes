#!/usr/bin/env python3
"""
Aerodrome Registry Change Review Tool

Compares staging vs production versions and shows detailed changes
for manual review before release.
"""
import json
import sys
from datetime import datetime
from typing import Dict, List, Set, Tuple

def load_json(filename: str) -> Dict:
    """Load and parse JSON file."""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"⚠️  File {filename} not found")
        return {}
    except json.JSONDecodeError as e:
        print(f"❌ Error parsing {filename}: {e}")
        return {}

def get_aerodrome_dict(data: Dict) -> Dict[str, Dict]:
    """Convert aerodrome list to dictionary keyed by ICAO code."""
    if not data or 'aerodromes' not in data:
        return {}
    return {a['icao']: a for a in data['aerodromes']}

def compare_aerodromes(prod_file: str = 'aerodromes.json', 
                      staging_file: str = 'aerodromes-staging.json') -> None:
    """Compare production and staging versions and show differences."""
    print("🔍 Comparing aerodrome registry versions...")
    print(f"📦 Production: {prod_file}")
    print(f"🚧 Staging: {staging_file}")
    print("-" * 60)
    
    # Load data
    prod_data = load_json(prod_file)
    staging_data = load_json(staging_file)
    
    if not staging_data:
        print("❌ No staging data found. Run sync first.")
        return
    
    prod_aerodromes = get_aerodrome_dict(prod_data)
    staging_aerodromes = get_aerodrome_dict(staging_data)
    
    prod_icaos = set(prod_aerodromes.keys())
    staging_icaos = set(staging_aerodromes.keys())
    
    # Summary statistics
    print(f"📊 Summary:")
    print(f"   Production aerodromes: {len(prod_aerodromes)}")
    print(f"   Staging aerodromes: {len(staging_aerodromes)}")
    print(f"   Net change: {len(staging_aerodromes) - len(prod_aerodromes):+d}")
    print()
    
    # New aerodromes
    new_icaos = staging_icaos - prod_icaos
    if new_icaos:
        print(f"✅ NEW AERODROMES ({len(new_icaos)}):")
        for icao in sorted(new_icaos)[:10]:  # Show first 10
            aerodrome = staging_aerodromes[icao]
            print(f"   + {icao}: {aerodrome['name']} ({aerodrome['country']})")
        if len(new_icaos) > 10:
            print(f"   ... and {len(new_icaos) - 10} more")
        print()
    
    # Removed aerodromes
    removed_icaos = prod_icaos - staging_icaos
    if removed_icaos:
        print(f"❌ REMOVED AERODROMES ({len(removed_icaos)}):")
        for icao in sorted(removed_icaos)[:10]:  # Show first 10
            aerodrome = prod_aerodromes[icao]
            print(f"   - {icao}: {aerodrome['name']} ({aerodrome['country']})")
        if len(removed_icaos) > 10:
            print(f"   ... and {len(removed_icaos) - 10} more")
        print()
    
    # Changed aerodromes
    common_icaos = prod_icaos & staging_icaos
    changed_icaos = []
    
    for icao in common_icaos:
        prod_aerodrome = prod_aerodromes[icao]
        staging_aerodrome = staging_aerodromes[icao]
        
        if prod_aerodrome != staging_aerodrome:
            changed_icaos.append(icao)
    
    if changed_icaos:
        print(f"🔄 CHANGED AERODROMES ({len(changed_icaos)}):")
        for icao in sorted(changed_icaos)[:10]:  # Show first 10
            prod_aerodrome = prod_aerodromes[icao]
            staging_aerodrome = staging_aerodromes[icao]
            
            print(f"   ~ {icao}: {staging_aerodrome['name']}")
            for key in ['name', 'country', 'timezone']:
                if prod_aerodrome.get(key) != staging_aerodrome.get(key):
                    print(f"     {key}: '{prod_aerodrome.get(key)}' → '{staging_aerodrome.get(key)}'")
        
        if len(changed_icaos) > 10:
            print(f"   ... and {len(changed_icaos) - 10} more")
        print()
    
    # Version info
    if staging_data.get('last_updated'):
        print(f"🕐 Staging last updated: {staging_data['last_updated']}")
    if prod_data.get('last_updated'):
        print(f"🕐 Production last updated: {prod_data.get('last_updated', 'unknown')}")
    
    print("-" * 60)
    
    # Recommendation
    total_changes = len(new_icaos) + len(removed_icaos) + len(changed_icaos)
    if total_changes == 0:
        print("✨ No changes detected - staging matches production")
    else:
        print(f"📋 Total changes: {total_changes}")
        print(f"💡 To release these changes, run: python3 release.py")
        
        # Warnings for significant changes
        if len(removed_icaos) > 100:
            print(f"⚠️  WARNING: {len(removed_icaos)} aerodromes removed - verify this is expected")
        if len(new_icaos) > 1000:
            print(f"⚠️  WARNING: {len(new_icaos)} aerodromes added - large data update")

if __name__ == "__main__":
    compare_aerodromes()
