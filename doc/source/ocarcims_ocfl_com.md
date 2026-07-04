# Orange County, FL

Support for curbside collection schedules provided by [Orange County Government](https://ocarcims.ocfl.net/), serving Orange County, Florida, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ocarcims_ocfl_com
      args:
        parcel_id: YOUR_PARCEL_ID
```

### Configuration Variables

**parcel_id**
*(string) (required)*

The 15-digit parcel ID for your property. Find it by searching your address at [ocarcims.ocfl.net](https://ocarcims.ocfl.net/) or [Orange County Property Appraiser](https://www.ocpafl.org/).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ocarcims_ocfl_com
      args:
        parcel_id: "012128690001243"  # Orange County Fire Station 27
```

## Returned Collection Types

| Collection type | Icon |
|---|---|
| Garbage | `mdi:trash-can` |
| Recycle / Recycling | `mdi:recycle` |
| Yard Waste | `mdi:leaf` |
| Bulk | `mdi:sofa` |
