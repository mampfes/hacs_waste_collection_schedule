# City of Canada Bay Council

Support for schedules provided by [City of Canada Bay Council](https://www.canadabay.nsw.gov.au).

Source for City of Canada Bay Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: canadabay_nsw_gov_au
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
    - name: canadabay_nsw_gov_au
      args:
        suburb: Concord
        street_name: Gipps Street
        street_number: 1A
```
