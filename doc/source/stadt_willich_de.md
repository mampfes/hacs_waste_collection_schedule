# GBW Gemeinschaftsbetrieb Willich

Support for schedules provided by [stadt-willich.de](https://www.stadt-willich.de) located in NRW, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_willich_de
      args:
        street: Zum Schickerhof
```

### Configuration Variables

**street**<br>
*(string) (required)*

## How to get the source arguments

Visit [stadt-willich.de](https://www.stadt-willich.de/de/dienstleistungen/abfallkalender-als-ical-datei/) and search for your address in the dropdown menu. The `street` argument should exactly match the result.
