#!/usr/bin/env python3
"""
Validation script for the aerodrome registry.
Validates aerodromes.json against schema.json
"""
import json
import jsonschema
from jsonschema import validate, ValidationError
import sys

def validate_aerodrome_data():
    """Validate the aerodrome registry data against the JSON schema."""
    try:
        # Load the schema
        with open('schema.json', 'r') as f:
            schema = json.load(f)
            
        # Load the data
        with open('aerodromes.json', 'r') as f:
            data = json.load(f)
            
        # Validate the data
        validate(instance=data, schema=schema)
        
        print("✅ Validation successful!")
        print(f"📊 Registry contains {data['total_count']} aerodromes")
        print(f"🕐 Last updated: {data['last_updated']}")
        print(f"📋 Version: {data['version']}")
        
        # Additional checks
        actual_count = len(data['aerodromes'])
        if actual_count != data['total_count']:
            print(f"⚠️  WARNING: total_count ({data['total_count']}) doesn't match actual count ({actual_count})")
            return False
            
        # Check for duplicate ICAO codes
        icao_codes = [aerodrome['icao'] for aerodrome in data['aerodromes']]
        duplicates = [code for code in set(icao_codes) if icao_codes.count(code) > 1]
        if duplicates:
            print(f"⚠️  WARNING: Duplicate ICAO codes found: {duplicates}")
            return False
            
        print("🎉 All validation checks passed!")
        return True
        
    except ValidationError as e:
        print(f"❌ Validation error: {e.message}")
        print(f"📍 Path: {' -> '.join(str(x) for x in e.path)}")
        return False
        
    except FileNotFoundError as e:
        print(f"❌ File not found: {e}")
        return False
        
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON: {e}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

if __name__ == "__main__":
    success = validate_aerodrome_data()
    sys.exit(0 if success else 1)
