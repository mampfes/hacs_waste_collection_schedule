# City of Philadelphia, PA

Support for schedules provided by [City of Philadelphia, PA](https://www.phila.gov/).

City of Philadelphia, PA, USA

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: phila_gov
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
    - name: phila_gov
      args:
        address: 1830 Fitzwater Street
```

## How to get the source arguments

Use your address as shown on the phila.gov trash/recycling collection-day search results.
