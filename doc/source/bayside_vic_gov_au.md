# Bayside Council

Support for schedules provided by [Bayside Council (Victoria)](https://www.bayside.vic.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bayside_vic_gov_au
      args:
        street_address: ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bayside_vic_gov_au
      args:
        street_address: 76 Royal Avenue Sandringham
```

## How to get the source argument

Enter your street address in a simple format as if you're searching on the online tool. Note that the first result will be selected if there are multiple search results.
For example:
- ✓ Good: `76 Royal Avenue Sandringham`

The search will return the first matching result. You can test your address on the [Bayside Council bin collection lookup tool](https://www.bayside.vic.gov.au/services/waste-and-recycling/bin-collection-day-look).