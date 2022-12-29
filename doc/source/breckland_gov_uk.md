# Breckland Council

Support for schedules provided by [Breckland Council](https://www.breckland.gov.uk/mybreckland)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: breckland_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS

```

### Configuration Variables

**POSTCODE**  
*(string) (required)*

**ADDRESS**  
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: breckland_gov_uk
      args:
        postcode: "IP22 2LJ"
        address: "glen travis"
```

You can find all relevant informations at [Breckland Council](https://www.breckland.gov.uk/mybreckland) homepage
use the POSTCODE -> click find address.
Choose your address. Please only use the first part of your address. If you got an error, use less charecters from address.


