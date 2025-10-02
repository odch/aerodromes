#!/usr/bin/env python3
"""
Aerodrome Registry Sync Script

Downloads and processes aerodrome data from OurAirports and OpenFlights
to create a comprehensive registry with ICAO codes, names, countries, and timezones.

Data Sources:
- OurAirports (https://ourairports.com) - Public Domain (Unlicense)
  Airport data by David Megginson and contributors
- OpenFlights (https://openflights.org) - Open Database License (ODbL)
  Timezone data by OpenFlights.org contributors
"""
import csv
import json
import os
import glob
import urllib.request
from datetime import datetime
from typing import Dict, List
from country_timezones import get_fallback_timezone

OURAIRPORTS_URL = "https://davidmegginson.github.io/ourairports-data/airports.csv"
OPENFLIGHTS_URL = "https://raw.githubusercontent.com/jpatokal/openflights/master/data/airports.dat"
INVALID_TIMEZONE_VALUES = [r'\N', 'N', '', 'NULL', '\\N']

def download_data(url: str) -> str:
    """Download data from URL and return as string."""
    try:
        with urllib.request.urlopen(url) as response:
            return response.read().decode('utf-8')
    except Exception as e:
        print(f"Error downloading {url}: {e}")
        raise

def extract_icao_code(row: Dict[str, str]) -> str:
    """Extract valid ICAO code from OurAirports row data."""
    icao_field = row.get('icao_code', '').strip()
    ident_field = row.get('ident', '').strip()
    
    if icao_field and len(icao_field) == 4:
        return icao_field
    elif ident_field and len(ident_field) == 4 and ident_field.isalpha():
        return ident_field
    return None

def process_ourairports_data(data: str) -> Dict[str, Dict[str, str]]:
    """Process OurAirports CSV data and extract active airports with valid ICAO codes."""
    airports = {}
    reader = csv.DictReader(data.splitlines())
    
    for row in reader:
        if row.get('type', '').strip() == 'closed':
            continue
            
        icao = extract_icao_code(row)
        if icao:
            airports[icao] = {
                'name': row.get('name', '').strip(),
                'country_code': row.get('iso_country', '').strip(),
                'latitude': float(row.get('latitude_deg', 0)) if row.get('latitude_deg') else 0,
                'longitude': float(row.get('longitude_deg', 0)) if row.get('longitude_deg') else 0
            }
    
    return airports

def process_openflights_data(data: str) -> Dict[str, str]:
    """Process OpenFlights data and extract timezone information."""
    timezones = {}
    
    for line in data.strip().split('\n'):
        if line.startswith('Airport ID'):
            continue
        
        try:
            fields = line.split(',')
            if len(fields) >= 12:
                icao = fields[5].strip('"')
                timezone = fields[11].strip('"')
                
                if icao and timezone and len(icao) == 4 and timezone not in INVALID_TIMEZONE_VALUES:
                    timezones[icao] = timezone
        except (IndexError, ValueError):
            continue
    
    return timezones

def load_aerodrome_overrides() -> List[Dict[str, str]]:
    """Load aerodrome overrides from modifications/overrides/ directory."""
    overrides = []
    overrides_dir = 'modifications/overrides'
    
    if not os.path.exists(overrides_dir):
        print(f"📝 No overrides directory found at {overrides_dir}")
        return overrides
    
    json_files = glob.glob(os.path.join(overrides_dir, '*.json'))
    
    for file_path in json_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                file_overrides = json.load(f)
                if isinstance(file_overrides, list):
                    overrides.extend(file_overrides)
                    print(f"📝 Loaded {len(file_overrides)} overrides from {os.path.basename(file_path)}")
                else:
                    print(f"⚠️  Skipping {file_path}: expected JSON array")
        except (json.JSONDecodeError, FileNotFoundError) as e:
            print(f"⚠️  Error loading {file_path}: {e}")
    
    return overrides

def build_registry(airports: Dict[str, Dict[str, str]], timezones: Dict[str, str], overrides: List[Dict[str, str]] = None) -> List[Dict[str, str]]:
    """Build the final aerodrome registry with timezone assignment, including overrides."""
    registry = []
    stats = {'matched': 0, 'fallback': 0, 'overrides': 0, 'overridden': 0}
    
    override_lookup = {override['icao']: override for override in (overrides or []) if 'icao' in override}
    
    for icao, data in airports.items():
        if icao in override_lookup:
            override_data = override_lookup[icao]
            entry = {
                'icao': icao,
                'name': override_data.get('name', data['name']),
                'country': override_data.get('country', data['country_code']),
                'timezone': override_data.get('timezone', 'UTC')
            }
            stats['overridden'] += 1
            print(f"🔄 Overriding {icao} with custom data")
        else:
            timezone = timezones.get(icao)
            if timezone:
                stats['matched'] += 1
            else:
                timezone = get_fallback_timezone(data['country_code'])
                stats['fallback'] += 1
            
            entry = {
                'icao': icao,
                'name': data['name'],
                'country': data['country_code'],
                'timezone': timezone
            }
        
        registry.append(entry)
    
    existing_icaos = {entry['icao'] for entry in registry}
    for override in (overrides or []):
        if 'icao' in override and override['icao'] not in existing_icaos:
            entry = {
                'icao': override['icao'],
                'name': override.get('name', ''),
                'country': override.get('country', ''),
                'timezone': override.get('timezone', 'UTC')
            }
            registry.append(entry)
            stats['overrides'] += 1
            print(f"➕ Adding new aerodrome {override['icao']} from overrides")
    
    registry.sort(key=lambda x: x['icao'])
    return registry, stats

def main():
    """Main sync process."""
    print("🔄 Starting aerodrome registry sync...")
    
    print("📥 Downloading data sources...")
    ourairports_data = download_data(OURAIRPORTS_URL)
    openflights_data = download_data(OPENFLIGHTS_URL)
    
    print("🔍 Processing OurAirports data...")
    airports = process_ourairports_data(ourairports_data)
    print(f"📊 Found {len(airports)} airports with ICAO codes")
    
    print("🔍 Processing OpenFlights timezone data...")
    timezones = process_openflights_data(openflights_data)
    print(f"📊 Found {len(timezones)} airports with timezone data")
    
    print("📝 Loading aerodrome overrides...")
    overrides = load_aerodrome_overrides()
    
    print("🏗️ Building aerodrome registry...")
    aerodromes, stats = build_registry(airports, timezones, overrides)
    
    try:
        with open('VERSION', 'r') as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = '1.0.0'
    
    registry = {
        'version': version,
        'last_updated': datetime.now().strftime('%Y-%m-%dT%H:%M:%S%z'),
        'total_count': len(aerodromes),
        'aerodromes': aerodromes
    }
    
    output_file = 'aerodromes-staging.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(registry, f, indent=2, ensure_ascii=False)
    
    print("✅ Sync completed successfully!")
    print(f"📈 Total aerodromes: {len(aerodromes)}")
    print(f"🕒 Timezone matched from OpenFlights: {stats['matched']}")
    print(f"🌍 Timezone from country fallback: {stats['fallback']}")
    print(f"🔄 Existing aerodromes overridden: {stats['overridden']}")
    print(f"➕ New aerodromes from overrides: {stats['overrides']}")
    print(f"💾 Registry saved to: {output_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        raise
