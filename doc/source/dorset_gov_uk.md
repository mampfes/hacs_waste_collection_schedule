# Dorset Council

Support for schedules provided by [Dorset Council](https://www.dorsetcouncil.gov.uk), The local authority for the non-metropolitan county of Dorset in England.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: dorset_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: dorset_gov_uk
      args:
        uprn: "100040606062"
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
