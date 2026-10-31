# Ipswich Borough Council

Support for schedules provided by [Ipswich Borough Council](https://www.ipswich.gov.uk).

Source for waste collection schedules provided by Ipswich Borough Council, UK.

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ipswich_gov_uk
      args:
        location_id: 549
```

## How to get the source arguments

Visit https://app.ipswich.gov.uk/bin-collection-better-recycling/ and search for your street. Once your schedule is displayed the URL ends with /weeks/<number>: use that number as the location ID (e.g. 549). Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
