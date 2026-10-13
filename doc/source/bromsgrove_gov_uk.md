# Bromsgrove & Redditch Councils

Support for schedules provided by [Bromsgrove & Redditch Councils](https://bromsgrove.gov.uk).

Source for the shared bin collection lookup used by Bromsgrove District Council and Redditch Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bromsgrove_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
        council: COUNCIL
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (required)*

**council**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bromsgrove_gov_uk
      args:
        uprn: '10094552413'
        postcode: B61 8DA
```

## How to get the source arguments

Find your UPRN at [FindMyAddress.co.uk](https://www.findmyaddress.co.uk/) and enter it with the postcode of the same address. The council is `bromsgrove` (default) or `redditch`.
