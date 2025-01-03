# Rother District Council

Support for schedules provided by [Rother District Council](https://www.rother.gov.uk), serving Rother District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rother_gov_uk
      args:
        uprn: "UNIQUE_PROPERTY_REFERENCE_NUMBER"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rother_gov_uk
      args:
        uprn: "10002653856"
        
```

## How to get the UPRN

Use your address to search for your bin days on the council's website [rother.gov.uk/findmynearest](https://www.rother.gov.uk/findmynearest/). The UPRN will be displayed above the bin collection days.
