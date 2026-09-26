# South Ribble Borough Council

Support for schedules provided by [South Ribble Borough Council](https://www.southribble.gov.uk).

Source for southribble.gov.uk services for South Ribble Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: southribble_gov_uk
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
    - name: southribble_gov_uk
      args:
        postcode: PR25 1DH
        uprn: '100012755948'
```

## How to get the source arguments

Go to https://www.southribble.gov.uk/bincollectiondays and enter your postcode. The UPRN is the option value of your address in the address dropdown (browser dev tools); an unknown UPRN is reported with the addresses the form lists for your postcode.
