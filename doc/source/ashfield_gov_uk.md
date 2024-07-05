# Ashfield District Council

Support for schedules provided by [Ashfield District Council](https://www.ashfield.gov.uk/), serving Ashfield district in Nottinghshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ashfield_gov_uk
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Should exactly match the address as it appears on the Ashfield District Council website when you search for your address.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: ashfield_gov_uk
      args:
        address: "101 Main Street, Huthwaite, Sutton In Ashfield, NG17 2LQ"
```
