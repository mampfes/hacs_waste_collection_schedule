# Mount Alexander Shire Council

Support for schedules provided by [Mount Alexander Shire Council](https://www.mountalexander.vic.gov.au).

Source for Mount Alexander Shire Council, VIC, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mount_alexander_vic_gov_au
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
    - name: mount_alexander_vic_gov_au
      args:
        address: 123 Main Road Campbells Creek Victoria 3451
```

## How to get the source arguments

Enter your full street address as it appears on the council website, e.g. '1 Mostyn Street Castlemaine Victoria 3450'.
