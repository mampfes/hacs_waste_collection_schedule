# City of Rockingham

Support for schedules provided by [City of Rockingham](https://rockingham.wa.gov.au/your-services/waste-and-recycling/bin-collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rockingham_wa_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rockingham_wa_gov_au
      args:
        suburb: Baldivis
        street_name: Settlers Avenue
        street_number: 20
```

## How to get the source arguments

