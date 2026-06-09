# City of Mandurah

Support for schedules provided by [City of Mandurah](https://www.mandurah.wa.gov.au/live/waste-and-recycling/bin-collections), Western Australia.

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
        address: "3 Peel ST MANDURAH"
```

## How to get the source arguments

Visit the [City of Mandurah bin collections](https://www.mandurah.wa.gov.au/live/waste-and-recycling/bin-collections) page and search for your address.
