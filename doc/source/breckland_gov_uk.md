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
        prn: UPRN
```

### Configuration Variables

**POSTCODE**  
*(string) (optional)*

**ADDRESS**  
*(string) (optional)*

**UPRN**  
*(string) (optional)*

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: breckland_gov_uk
      args:
        postcode: "IP22 2LJ"
        address: "glen travis"
```

```yaml
waste_collection_schedule:
    sources:
    - name: breckland_gov_uk
      args:
        uprn: "10011977093"
```

If uprn is provided, only uprn is used. Otherwise postcode and address are required.

You can find all relevant information at [Breckland Council](https://www.breckland.gov.uk/mybreckland) homepage. Use the POSTCODE -> click find address.
Choose your address. Please only use the first part of your address. If you got an error, use less characters from address.

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by going to [Find My Address](https://www.findmyaddress.co.uk/) and providng your address details.
