# London Borough of Camden

Support for schedules provided by [London Borough of Camden](https://www.camden.gov.uk/), serving Camden, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: camden_gov_uk
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
    - name: camden_gov_uk
      args:
        uprn: 5061647
        
```

## How to get the source argument

Select your address on <https://environmentservices.camden.gov.uk>. You get redirected to your collection overview. The URL contains your UPRN (`https://environmentservices.camden.gov.uk/property/{UPRN}`)

An other way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
