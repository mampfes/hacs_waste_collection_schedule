# Tewkesbury City Council

Support for upcoming schedules provided by [Tewkesbury City Council](https://www.tewkesbury.gov.uk/waste-and-recycling), serving Tewkesbury (UK) and areas of Gloucestershire.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: tewkesbury_gov_uk
      args:
        postcode: POSTCODE
```

```yaml
waste_collection_schedule:
    sources:
    - name: tewkesbury_gov_uk
      args:
        uprn: UNIQUE PROPERTY REFERENCE NUMBER
```

### Configuration Variables

**POSTCODE**  
*(string) (optional)*  
Not all addresses are supported by postcode. Then you have to provide a UPRN.

**UPRN**  
*(string) (optional)*

Either `postcode` or `uprn` must be provided.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: tewkesbury_gov_uk
      args:
        postcode: "GL20 5TT"
```

```yaml
waste_collection_schedule:
    sources:
    - name: tewkesbury_gov_uk
      args:
        uprn: 100120544973
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
