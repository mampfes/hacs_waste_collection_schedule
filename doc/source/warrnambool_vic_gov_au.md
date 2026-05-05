# Warrnambool City Council

Support for schedules provided by [Warrnambool City Council](https://www.warrnambool.vic.gov.au/kerbside-bin-collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: warrnambool_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: warrnambool_vic_gov_au
      args:
        street_address: 3 Kiama Ave WARRNAMBOOL VIC 3280
```

## How to get the source arguments

Visit the [Warrnambool City Council kerbside bin collection](https://www.warrnambool.vic.gov.au/kerbside-bin-collection) page and search for your address in the bin collection lookup. The address should be in the format used by the lookup, e.g. "3 Kiama Ave WARRNAMBOOL VIC 3280".
