# Sutherland Shire Council

Support for waste collection schedules provided by [Sutherland Shire Council](https://www.sutherlandshire.nsw.gov.au), NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sutherlandshire_nsw_gov_au
      args:
        suburb: SUBURB
        street: STREET NAME
        house_number: HOUSE NUMBER
```

### Arguments

| Argument | Description |
|----------|-------------|
| `suburb` | Suburb name, as normally written (e.g. `Bonnet Bay`) |
| `street` | Street name, as normally written (e.g. `Cleveland Place`) |
| `house_number` | House number (e.g. `5`) |

### Example

```yaml
waste_collection_schedule:
  sources:
    - name: sutherlandshire_nsw_gov_au
      args:
        suburb: Bonnet Bay
        street: Cleveland Place
        house_number: "5"
```

## How to find your arguments

Enter your `suburb`, `street` and `house_number` exactly as they appear in your normal postal address. The source looks up your address automatically using the same online services map the council publishes at [sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/bin-collection](https://www.sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/bin-collection), so there's no dropdown list to match against.

## Collection types

| Type | Description |
|------|-------------|
| Garbage | Red-lid bin, collected weekly |
| Recycling | Yellow-lid bin, collected fortnightly |
| Garden Waste | Green-lid bin, collected fortnightly (alternating with Recycling) |

The fortnightly recycling/garden waste schedule is determined automatically from your collection zone and collection day, both returned by the council's online services map for your address.
