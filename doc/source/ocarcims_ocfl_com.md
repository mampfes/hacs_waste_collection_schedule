# Orange County, FL

Support for curbside collection schedules provided by [Orange County Government](https://ocarcims.ocfl.net/), serving Orange County, Florida, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ocarcims_ocfl_com
      args:
        parcel_id: "123456789012345"
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
        parcel_id: "123456789012345"
```

## Returned Collection Types

| Collection type | Icon |
|---|---|
| Garbage | `mdi:trash-can` |
| Recycle / Recycling | `mdi:recycle` |
| Yard Waste | `mdi:leaf` |
| Bulk | `mdi:sofa` |
