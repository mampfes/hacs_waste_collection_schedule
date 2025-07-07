# Clarence City Council

Support for schedules provided by [Clarence City Council](https://www.chesterfield.gov.uk/bins-and-recycling/bin-collections/check-bin-collections.aspx)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ccc_tas_gov_au
      args:
        address: "<Street Address>"
```

### Configuration Variables

**address**  
*(string) (required)*

This is required to unambiguously identify the property. The api will search and return a formatted version for use in further api requests so it's pretty relaxed about what you put in.

## Example using address

```yaml
waste_collection_schedule:
    sources:
    - name: ccc_tas_gov_au
      args:
        address: "80 Clarence St, Bellerive"
```


