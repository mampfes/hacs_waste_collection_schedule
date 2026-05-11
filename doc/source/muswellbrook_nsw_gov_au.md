# Muswellbrook Shire Council

Support for schedules provided by Muswellbrook Shire Council, NSW, Australia.

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

Your collection zone, e.g. `3a` or `5b`. Find your zone at <https://www.muswellbrook.nsw.gov.au/waste-collection/>.

Valid zones: `1a`, `1b`, `2a`, `2b`, `3a`, `3b`, `4a`, `4b`, `5a`, `5b`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muswellbrook_nsw_gov_au
      args:
        zone: 3a
```
