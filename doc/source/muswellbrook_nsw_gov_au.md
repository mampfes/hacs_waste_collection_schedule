# Muswellbrook Shire Council

Support for schedules provided by [Muswellbrook Shire Council](https://www.muswellbrook.nsw.gov.au).

Source for Muswellbrook Shire Council, NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muswellbrook_nsw_gov_au
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muswellbrook_nsw_gov_au
      args:
        zone: 3a
```

## How to get the source arguments

Find your collection zone at https://www.muswellbrook.nsw.gov.au/waste-collection/ and enter it as e.g. '3a' or '5b'.
