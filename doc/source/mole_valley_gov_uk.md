# Mole Valley District Council

Support for schedules provided by [Mole Valley District Council](https://www.molevalley.gov.uk/waste-recycling/calendar-collection-day/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mole_valley_gov_uk
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER_OR_NAME
```

### Configuration Variables

**postcode**
*(string) (required)*

Your property's postcode, e.g. `KT22 9BG`.

**house_number**
*(string) (required)*

Your house number or name, e.g. `17` or `Rose Cottage`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mole_valley_gov_uk
      args:
        postcode: "RH4 1LX"
        house_number: "79"
```

## Notes

This source returns only the **next** scheduled collection date for each waste type. Dates are updated automatically by the council's system as each collection passes.

Waste types supported:
- Refuse (black bin)
- Recycling (green bin)
- Garden Waste (brown lid) — only if subscribed to the garden waste service
- Food Waste
