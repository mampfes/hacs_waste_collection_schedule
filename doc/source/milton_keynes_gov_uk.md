# Milton Keynes council

Support for schedules provided by [Milton Keynes council](milton-keynes.gov.uk), serving Milton Keynes, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: milton_keynes_gov_uk
      args:
        uprn: "UPRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: milton_keynes_gov_uk
      args:
        uprn: "25032037"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
