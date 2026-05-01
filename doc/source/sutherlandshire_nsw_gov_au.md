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
| `suburb` | Suburb in UPPER CASE, exactly as shown in the dropdown (e.g. `BONNET BAY`) |
| `street` | Street name, exactly as shown in the dropdown (e.g. `Cleveland Place`) |
| `house_number` | House number, exactly as shown in the dropdown (e.g. `5`) |

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

1. Visit the [Sutherland Shire bin day lookup](https://www.sutherlandshire.nsw.gov.au/living-here/waste-and-recycling/waste-information-booklet)
2. Select your **suburb** from the dropdown — use exactly this value (in UPPER CASE) for `suburb`
3. Select your **street** from the dropdown — use exactly this value for `street`
4. Select your **house number** from the dropdown — use exactly this value for `house_number`

The values must match the dropdown options exactly, including spacing and capitalisation.

## Collection types

| Type | Description |
|------|-------------|
| Garbage | Red-lid bin, collected weekly |
| Recycling | Yellow-lid bin, collected fortnightly |
| Garden Waste | Green-lid bin, collected fortnightly (alternating with Recycling) |

The fortnightly recycling/garden waste schedule is determined automatically from your collection zone, which is derived from the Waste Information Booklet PDF link returned by the council website.
