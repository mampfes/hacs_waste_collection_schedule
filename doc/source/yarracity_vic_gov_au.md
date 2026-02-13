# Yarra City Council (VIC)

Supports zones 1–10.

- Weekly: Rubbish + FOGO
- Fortnightly: Recycling (from 2025-07-04), Glass (from 2025-07-11)
- Holiday shifts: 26 Dec 2025 → 27 Dec, 3 Apr 2026 → 4 Apr

## Configuration via YAML

```yaml
waste_collection_schedule:
  sources:
    - name: yarracity_vic_gov_au
      args:
        zone: 10
