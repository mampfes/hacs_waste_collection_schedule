# South Lanarkshire Council

Support for schedules provided by [South Lanarkshire Council](https://wasteservices.southlanarkshire.gov.uk).

Source for South Lanarkshire Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southlanarkshire_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: southlanarkshire_gov_uk
      args:
        postcode: G73 2LF
        uprn: 484129473
```

## How to get the source arguments

Find your UPRN using FindMyAddress (https://www.findmyaddress.co.uk/search) or UPRN.uk (https://uprn.uk) - search for your address and note the UPRN shown. Alternatively, visit https://wasteservices.southlanarkshire.gov.uk/PublicDashboard, enter your postcode, select your property, then inspect the dropdown option (right-click > Inspect Element) and note the numeric value= attribute.
