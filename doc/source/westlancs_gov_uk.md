# West Lancashire Council

Support for schedules provided by [West Lancashire Council](https://westlancs.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: westlancs_gov_uk
      args:
        postcode: "WN8 9QR"
        uprn: "10012340497"
```

### Configuration Variables

**postcode**  
*(string) (required)*

The postcode of your address. Use uppercase format with or without space (e.g., "WN8 9QR" or "WN89QR").

**uprn**  
*(string) (required)*

The Unique Property Reference Number for your address. This ensures the correct address is selected when multiple properties share a postcode.

To find your UPRN:
1. Visit https://your.westlancs.gov.uk/yourwestlancs.aspx
2. Enter your postcode in the search box
3. Look for your address in the list - the UPRN is shown in the table (e.g., "10012340497")

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: westlancs_gov_uk
      args:
        postcode: "WN8 9QR"
        uprn: "10012340497"
        
sensor:
  - platform: waste_collection_schedule
    name: Refuse Collection
    details_format: "upcoming"
    types:
      - Refuse

  - platform: waste_collection_schedule
    name: Recycling Collection
    details_format: "upcoming"
    types:
      - Recycling

  - platform: waste_collection_schedule
    name: Garden Waste Collection
    details_format: "upcoming"
    types:
      - Garden Waste
```

## How It Works

The source queries the West Lancashire Council website using your postcode and UPRN to ensure the correct property is selected. It then retrieves the next collection dates for each waste type (Refuse, Recycling, and Garden Waste if subscribed).