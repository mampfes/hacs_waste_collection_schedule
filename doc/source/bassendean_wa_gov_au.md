# Town of Bassendean

Support for schedules provided by [Town of Bassendean](https://www.bassendean.wa.gov.au).

Source for Town of Bassendean waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bassendean_wa_gov_au
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
    - name: bassendean_wa_gov_au
      args:
        address: 16 Kenny St, Bassendean
```

## How to get the source arguments

Enter your street address within the Town of Bassendean (e.g. '16 Kenny St, Bassendean').
