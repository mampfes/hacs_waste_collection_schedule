# City of Newcastle (NSW)

Weekly rubbish (red) and alternating **recycling** / **organics** on the same weekday.

## Configuration via YAML

```yaml
waste_collection_schedule:
  sources:
    - name: newcastle_nsw_gov_au
      args:
        weekday: tuesday
        recycling_seed: 2025-01-07
```
