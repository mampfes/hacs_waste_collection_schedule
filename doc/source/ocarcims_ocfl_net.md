# Orange County, FL

Support for curbside collection schedules provided by [Orange County Government](https://ocarcims.ocfl.net/), serving unincorporated Orange County, Florida, USA.

> **Note:** This source only works for properties in **unincorporated Orange County**. Residents of incorporated cities within Orange County (Orlando, Winter Park, Apopka, Maitland, etc.) have separate waste services and are not supported by this source.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ocarcims_ocfl_net
      args:
        parcel_id: YOUR_PARCEL_ID
```

### Configuration Variables

**parcel_id**
*(string) (required)*

The 15-digit parcel ID for your property.

## How to find your `parcel_id`

1. Go to [ocarcims.ocfl.net](https://ocarcims.ocfl.net/) or [Orange County Property Appraiser](https://www.ocpafl.org/).
2. Search for your address.
3. The 15-digit parcel ID appears in the search results on either site.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ocarcims_ocfl_net
      args:
        parcel_id: "012128690001243"  # Orange County Fire Station 27
```

## Bin types returned

| Provider description | Returned type | Icon |
|---|---|---|
| Garbage | Garbage | `Icons.GENERAL_WASTE` |
| Recycle / Recycling | Recycling | `Icons.RECYCLING` |
| Yard Waste | Yard Waste | `Icons.GARDEN` |
| Bulk / Large Item | Large Item | `Icons.BULKY` |
