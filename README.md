# Aerodrome Registry

A comprehensive registry of all aerodromes worldwide that have ICAO codes. This serves as a single source of truth for multiple projects requiring aerodrome data.

## Overview

This registry contains essential information for each aerodrome:
- **ICAO Code**: 4-letter international identifier
- **Name**: Official aerodrome name
- **Country**: Country location
- **Timezone**: IANA timezone identifier

## Data Format

The registry uses JSON format for maximum compatibility and ease of integration:

```json
{
  "version": "1.0.0",
  "last_updated": "2025-09-22T22:40:31+02:00",
  "total_count": 4,
  "aerodromes": [
    {
      "icao": "KJFK",
      "name": "John F. Kennedy International Airport",
      "country": "United States",
      "timezone": "America/New_York"
    }
  ]
}
```

## Files

- `aerodromes.json` - Main registry file containing all aerodrome data
- `schema.json` - JSON Schema for data validation
- `README.md` - This documentation file

## Usage

### For Nightly Database Imports

Most projects can import this data directly into their databases:

**Python Example:**
```python
import json
import requests
from datetime import datetime

def import_aerodromes():
    with open('aerodromes.json', 'r') as f:
        data = json.load(f)
    
    for aerodrome in data['aerodromes']:
        # Insert into your database
        insert_aerodrome(
            icao=aerodrome['icao'],
            name=aerodrome['name'],
            country=aerodrome['country'],
            timezone=aerodrome['timezone']
        )
    
    print(f"Imported {data['total_count']} aerodromes")
```

**Node.js Example:**
```javascript
const fs = require('fs').promises;

async function importAerodromes() {
    const data = JSON.parse(await fs.readFile('aerodromes.json', 'utf8'));
    
    for (const aerodrome of data.aerodromes) {
        await insertAerodrome({
            icao: aerodrome.icao,
            name: aerodrome.name,
            country: aerodrome.country,
            timezone: aerodrome.timezone
        });
    }
    
    console.log(`Imported ${data.total_count} aerodromes`);
}
```

### Data Validation

Use the provided JSON Schema to validate data integrity:

```bash
# Using ajv-cli
npm install -g ajv-cli
ajv validate -s schema.json -d aerodromes.json
```

```python
# Using jsonschema library
import json
import jsonschema

with open('schema.json', 'r') as f:
    schema = json.load(f)

with open('aerodromes.json', 'r') as f:
    data = json.load(f)

jsonschema.validate(data, schema)
print("Data is valid!")
```

## Data Sources

This registry is built using the following open data sources:

### Primary Data Sources

1. **OurAirports** (https://ourairports.com)
   - **License**: Public Domain (Unlicense)
   - **Usage**: Airport names, locations, and ICAO codes
   - **Attribution**: David Megginson and contributors

2. **OpenFlights** (https://openflights.org)
   - **License**: Open Database License (ODbL)
   - **Usage**: Timezone data for airports
   - **Attribution**: OpenFlights.org contributors

### Data Processing

- Airport data is sourced primarily from OurAirports (public domain)
- Timezone information is enhanced using OpenFlights data where available
- Fallback timezone mapping is applied based on country location
- The registry includes both 'icao_code' and 'ident' fields from OurAirports to ensure comprehensive coverage

## Maintenance

### Automated Workflow

This registry uses a **GitOps workflow** with automated data synchronization and manual review/release process.

#### 🤖 Automated Sync Process

**Every Monday at 6:00 AM UTC** (or manually triggered), GitHub Actions automatically:

1. **Downloads** fresh data from OurAirports and OpenFlights
2. **Processes** data using `sync_aerodromes.py`
3. **Creates** `aerodromes-staging.json` with latest information
4. **Compares** staging vs production data
5. **If changes detected**:
   - Commits staging file to repository
   - Generates detailed change summary
   - **Creates GitHub Issue** for manual review

#### 👤 Manual Review & Release

When automation detects changes, **you receive a GitHub Issue** with:
- Detailed change summary and statistics
- Instructions for next steps
- Automatic labels for easy tracking

**Your options:**
- **Review**: Run `python3 review_changes.py` to see detailed changes
- **Approve**: Run `python3 release.py` to promote staging → production
- **Reject**: Do nothing, changes remain in staging only

#### 🔒 Safety Features

- **Production never touched by automation** - Always requires manual approval
- **Automatic backups** created before each release
- **Rollback capability** if issues arise
- **Data validation** before promotion
- **Clear audit trail** through Git commits and Issues

#### 📁 Key Files

- **`aerodromes.json`** - 🟢 PRODUCTION (what applications consume)
- **`aerodromes-staging.json`** - 🟡 STAGING (automated updates)
- **`sync_aerodromes.py`** - Downloads and processes source data
- **`review_changes.py`** - Shows differences between staging and production  
- **`release.py`** - Promotes staging to production with backups

### Manual Maintenance

#### Adding Individual Aerodromes (Not Recommended)

For emergency additions only. **Prefer the automated sync process** for data quality.

1. Ensure the aerodrome has a valid 4-letter ICAO code
2. Add entry to the `aerodromes` array in `aerodromes.json`
3. Update `total_count` field
4. Update `last_updated` timestamp
5. Validate against schema
6. Commit changes

## Contributing

1. Fork the repository
2. Make your changes
3. Validate data against schema
4. Submit a pull request with description of changes

## License

### Registry Software & Code
This project (code, scripts, and documentation) is licensed under the **MIT License**. See the [LICENSE](LICENSE) file for details.

### Data Licensing & Attribution

This registry uses data from the following sources with their respective licenses:

1. **OurAirports Data**: Public Domain (Unlicense)
   - No attribution required, but we credit David Megginson and contributors
   - Source: https://github.com/davidmegginson/ourairports-data

2. **OpenFlights Data**: Open Database License (ODbL) v1.0
   - Requires attribution and share-alike for derivative works
   - Source: https://openflights.org
   - License: https://opendatacommons.org/licenses/odbl/1-0/

### Usage Compliance

**If you use this registry:**
- ✅ You can use it freely for any purpose (commercial or non-commercial)
- ✅ Attribution is appreciated but not legally required for the registry itself
- ✅ The underlying airport data is largely public domain

**If you create derivative works:**
- 📝 Please maintain attribution to data sources (good practice)
- 📝 For works using OpenFlights-derived data, follow ODbL requirements
- 📝 Consider contributing improvements back to the community

### Disclaimer

This data is not suitable for navigation. The maintainers assume no responsibility for accuracy and no liability for results obtained or damages incurred from using this data.

## Support

For questions or issues, please create an issue in the repository or contact the maintainers.
