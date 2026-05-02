# City of Kwinana

Support for schedules provided by [City of Kwinana](https://www.kwinana.wa.gov.au/property-and-pets/waste-and-recycling/your-bins-and-collection-day), serving the Kwinana, Wellard, and surrounding areas of Western Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kwinana_wa_gov_au
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
    - name: kwinana_wa_gov_au
      args:
        address: "25 Breccia Parade WELLARD"
```

## How to get the source arguments

Visit the [City of Kwinana bin collection](https://www.kwinana.wa.gov.au/property-and-pets/waste-and-recycling/your-bins-and-collection-day) page and search for your address.
