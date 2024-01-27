# London Borough of Hounslow

Support for schedules provided by [London Borough of Hounslow](https://hounslow.gov.uk), serving London Borough of Hounslow, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hounslow_gov_uk
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
    - name: hounslow_gov_uk
      args:
        uprn: "100021552942"
        
```

## How to get the source argument

### Using findmyaddress.co.uk

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

### Using browsers developer tools

- Go to <https://www.hounslow.gov.uk/homepage/86/recycling_and_waste_collection_day_finder#collectionday>
- Enter your postcode and click "Find address"
- Right on the `Pick an address` dropdown and select `Inspect` or `Inspect Element`
- Expand the `select` element and find the `option` element with the you address
- The first number in the `value` attribute is your UPRN
