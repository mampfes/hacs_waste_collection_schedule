# City of Mandurah

Support for schedules provided by [City of Mandurah](https://www.mandurah.wa.gov.au/live/waste-and-recycling/bin-collections).

Source for City of Mandurah waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mandurah_wa_gov_au
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
    - name: mandurah_wa_gov_au
      args:
        address: Estuary RD BOUVARD
```

## How to get the source arguments

Enter your street address including suburb. Search at https://www.mandurah.wa.gov.au/live/waste-and-recycling/bin-collections
