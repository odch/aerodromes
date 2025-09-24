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
    """Process OurAirports CSV data and extract airports with valid ICAO codes."""
    airports = {}
    reader = csv.DictReader(data.splitlines())
    
    for row in reader:
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

def build_registry(airports: Dict[str, Dict[str, str]], timezones: Dict[str, str]) -> List[Dict[str, str]]:
    """Build the final aerodrome registry with timezone assignment."""
    registry = []
    timezone_stats = {'matched': 0, 'fallback': 0}
    
    for icao, data in airports.items():
        timezone = timezones.get(icao)
        if timezone:
            timezone_stats['matched'] += 1
        else:
            timezone = get_fallback_timezone(data['country_code'])
            timezone_stats['fallback'] += 1
        
        registry.append({
            'icao': icao,
            'name': data['name'],
            'country': data['country_code'],
            'timezone': timezone
        })
    
    registry.sort(key=lambda x: x['icao'])
    return registry, timezone_stats

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
    
    print("🏗️ Building aerodrome registry...")
    aerodromes, stats = build_registry(airports, timezones)
    
    # Read version from VERSION file
    try:
        with open('VERSION', 'r') as f:
            version = f.read().strip()
    except FileNotFoundError:
        version = '1.0.0'  # Fallback if VERSION file missing
    
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
    print(f"💾 Registry saved to: {output_file}")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"❌ Error during sync: {e}")
        raise
