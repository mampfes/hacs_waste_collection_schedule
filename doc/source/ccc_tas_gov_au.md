# Clarence City Council

Support for schedules provided by [Clarence City Council](https://www.ccc.tas.gov.au).

The greater Eastern Shore of Hobart

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ccc_tas_gov_au
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
    - name: ccc_tas_gov_au
      args:
        address: 80 Clarence St
```

## How to get the source arguments

Enter your street address, e.g. `123 Clarence St`; the council's address search picks the first match.
