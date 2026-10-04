# Sevenoaks District Council

Support for schedules provided by [Sevenoaks District Council](https://www.sevenoaks.gov.uk).

Source for Sevenoaks District Council waste collection schedule

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sevenoaks_gov_uk
      args:
        property_id: PROPERTY_ID
```

### Configuration Variables

**property_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sevenoaks_gov_uk
      args:
        property_id: 51621
```

## How to get the source arguments

Visit https://sevenoaks-dc-host01.oncreate.app/w/webpage/waste-collection-day, enter your postcode (with the space) and select your address; the numeric property id is the `id=` value in the resulting page URL.
