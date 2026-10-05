# Port Stephens Council

Support for schedules provided by [Port Stephens Council](https://www.portstephens.nsw.gov.au/).

Source for Port Stephens Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: portstephens_nsw_gov_au
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
    - name: portstephens_nsw_gov_au
      args:
        suburb: Soldiers Point
        street_name: Lyndel Close
        street_number: '2'
```
