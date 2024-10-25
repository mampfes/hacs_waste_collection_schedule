# Cardiff Council

Support for schedules provided by [Carmarthenshire County Council](https://www.carmarthenshire.gov.wales/home/council-services/), serving Carmathenshire, Wales (UK).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: carmarthenshire_gov_wales
      args:
        uprn: UPRN
```

### Configuration Variables

**UPRN**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: carmarthenshire_gov_wales
      args:
        uprn: "10009546468"
```

## How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
