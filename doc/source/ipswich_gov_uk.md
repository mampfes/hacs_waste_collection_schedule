# Ipswich Borough Council

Support for waste collection schedules provided by [Ipswich Borough Council](https://www.ipswich.gov.uk), serving Ipswich, Suffolk, UK.

## Local Government Reorganisation note
This source **only** serves the areas covered by the **existing** Ipswich Borough Council, and not the upcoming Ipswich & South Suffolk Council.

During the ongoing local government reorganisation (LGR) in Suffolk, please continue to use the source for your current area as long as it's still working. New sources for the new Ipswich & South Suffolk Council are not expected to be live until at least April 2028, when the council itself officially comes into being.

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
