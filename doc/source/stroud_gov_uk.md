# Stroud District Council

Support for schedules provided by [Stroud District Council](https://stroud.gov.uk), serving Stroud, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stroud_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
        
```

### Configuration Variables

**postcode**  
*(String) (required)*

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: stroud_gov_uk
      args:
        postcode: GL6 9BW
        uprn: "100120517945"
        
```

## How to get the source argument

Use your postcode as the `postcode` argument and your Unique Property Reference Number (UPRN) as the `uprn` argument.

You can see your UPRN in the address bar after searching your address here: <https://www.stroud.gov.uk/my-house>

Another easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
