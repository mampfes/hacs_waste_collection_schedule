# Midlothian Council (my.midlothian.gov.uk)

This source fetches bin collection dates for properties in Midlothian Council, Scotland, using the official council API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midlothian_gov_uk
      args:
        uprn: YOUR_UPRN
        postcode: YOUR_POSTCODE
```

### Configuration Variables

- **uprn** _(string) (required)_: Unique Property Reference Number for your property (e.g., `120001401`).
- **postcode** _(string) (required)_: Postcode of your property (e.g., `EH26 8AG`).

You can find your UPRN and postcode on council tax bills or by contacting Midlothian Council.

### Example

```yaml
waste_collection_schedule:
  sources:
    - name: midlothian_gov_uk
      args:
        uprn: "120001401"
        postcode: "EH26 8AG"
```

This will fetch all available bin collection dates for the specified property.

### Returned Waste Types
- Food Collection Service
- Glass Collection Service
- Residual Collection Service
- Garden Collection Service
- Recycling Collection Service
- Card Collection Service

Each entry includes the collection date and type.
