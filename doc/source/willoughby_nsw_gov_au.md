# Willoughby City Council

Support for schedules provided by [Willoughby City Council](https://www.willoughby.nsw.gov.au).

Source for Willoughby City Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: willoughby_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: willoughby_nsw_gov_au
      args:
        address: 18 Crabbes Avenue, North Willoughby, NSW 2068
```

## How to get the source arguments

Visit the Willoughby City Council waste service dates page, search for your address, and use the address text as shown by the lookup.
