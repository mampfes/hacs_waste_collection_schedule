# Milton Keynes council

Support for schedules provided by [Milton Keynes council](milton-keynes.gov.uk).

Source for Milton Keynes council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: milton_keynes_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: milton_keynes_gov_uk
      args:
        uprn: 25032037
```

## How to get the source arguments

Find your UPRN at https://www.findmyaddress.co.uk/ by searching for your address.
