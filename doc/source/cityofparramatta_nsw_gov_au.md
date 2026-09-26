# City of Parramatta

Support for schedules provided by [City of Parramatta](https://www.cityofparramatta.nsw.gov.au).

Source script for cityofparramatta.nsw.gov.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cityofparramatta_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cityofparramatta_nsw_gov_au
      args:
        address: 126 Church Street Parramatta
```

## How to get the source arguments

Enter your full address including the suburb. Example: `126 Church Street Parramatta`
