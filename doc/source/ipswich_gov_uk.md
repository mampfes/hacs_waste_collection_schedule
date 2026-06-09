# Ipswich Borough Council

Support for waste collection schedules provided by [Ipswich Borough Council](https://www.ipswich.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ipswich_gov_uk
      args:
        location_id: LOCATION_ID
```

### Configuration Variables

**location_id**
*(integer) (required)*

A numeric ID that identifies your street/address in the council's collection portal.

## How to find your `location_id`

1. Go to <https://app.ipswich.gov.uk/bin-collection-better-recycling/>
2. Search for and select your street.
3. Your collection schedule will be displayed and the browser URL will change to something like:

   ```
   https://app.ipswich.gov.uk/bin-collection-better-recycling/weeks/549
   ```

4. The number at the end of the URL (`549` in the example above) is your `location_id`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ipswich_gov_uk
      args:
        location_id: 549
```

## Bin types returned

The source maps the council's bin descriptions to the following waste types:

| Council description | Returned type   | Icon                   |
|---------------------|-----------------|------------------------|
| General Waste       | General Waste   | `mdi:trash-can`        |
| Recycling           | Recycling       | `mdi:recycle`          |
| Garden Waste        | Garden Waste    | `mdi:leaf`             |
| Food Waste          | Food Waste      | `mdi:food-apple`       |

Unknown bin types are returned with their original name and a generic `mdi:trash-can` icon.
