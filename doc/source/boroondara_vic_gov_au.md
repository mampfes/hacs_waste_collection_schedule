# City of Boroondara

Support for schedules provided by [City of Boroondara](https://www.boroondara.vic.gov.au/services/waste-and-recycling/bins/find-your-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: boroondara_vic_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Street address within the City of Boroondara.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: boroondara_vic_gov_au
      args:
        address: 211 Mont Albert Road, Surrey Hills
```

## How to get the source arguments

Enter your street address as it appears on the [Boroondara bin day finder](https://www.boroondara.vic.gov.au/services/waste-and-recycling/bins/find-your-bin-day). Include the suburb name for best results.

Collection types returned:

- **Recycling** — weekly
- **General Waste** — fortnightly
- **FOGO** (Food Organics and Garden Organics) — fortnightly, same day as General Waste
