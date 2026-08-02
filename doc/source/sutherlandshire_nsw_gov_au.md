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
| `suburb` | Suburb (e.g. `BONNET BAY`) |
| `street` | Street name spelled out in full (e.g. `Cleveland Place`) |
| `house_number` | House number (e.g. `5`) |

### Example

```yaml
waste_collection_schedule:
  sources:
    - name: sutherlandshire_nsw_gov_au
      args:
        suburb: BONNET BAY
        street: Cleveland Place
        house_number: "5"
```

## How to find your arguments

Use your address as it appears on council correspondence, with the street type
spelled out in full (`Street`, `Place`, `Avenue`, …). If the house number isn't
found, the integration suggests the known numbers on your street. You can
check your address on the council's
[bin collection page](https://www.sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/bin-collection).

## Collection types

| Type | Description |
|------|-------------|
| Garbage | Red-lid bin, collected weekly |
| Recycling | Yellow-lid bin, collected fortnightly (weekly for some unit blocks) |
| Garden Waste | Green-lid bin, collected fortnightly (alternating with Recycling) |

The schedule comes from the council's public property GIS layer (the same
data behind the council's own "When is my bin collected?" map), which carries
each property's collection weekday, zone and recycling frequency.
