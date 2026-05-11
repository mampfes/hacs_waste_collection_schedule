# London Borough of Hackney

Support for schedules provided by [London Borough of Hackney](https://www.hackney.gov.uk/), serving Hackney, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hackney_gov_uk
      args:
        uprn: "UPRN"
        postcode: "Postcode"
```

### Configuration Variables

**uprn**  
_(String | Integer) (required)_

**postcode**  
_(String) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hackney_gov_uk
      args:
        uprn: "5061647"
        postcode: "E8 4LL"
```

## How to get the source argument

Get your Unique Property Reference Number (UPRN) by going to <https://www.findmyaddress.co.uk/> and entering your address details.
