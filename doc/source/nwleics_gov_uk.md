# North West Leicestershire District Council

Source for www.nwleics.gov.uk services for the city of North West Leicestershire District Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nwleics_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: nwleics_gov_uk
      args:
        uprn: "100030573554"
```

## How to get the source argument

The UPRN code can be found found using https://uprn.uk/
