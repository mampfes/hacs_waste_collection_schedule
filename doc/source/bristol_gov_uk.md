# Bristol City Council

Support for schedules provided by [Bristol City Council](https://www.bristol.gov.uk/residents/bins-and-recycling/bins-and-recycling-collection-dates), serving the city of Bristol, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bristol_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables
**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: bristol_gov_uk
      args:
        uprn: "17929"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.