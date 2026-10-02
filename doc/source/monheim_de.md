# Monheim am Rhein

Source for waste collection in Monheim am Rhein (NRW, Germany), provided by [monheim.de](https://www.monheim.de/leben-in-monheim/abfall-stadtreinigung/abfallkalender).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: monheim_de
      args:
        street: STREET_NAME
```

### Configuration Variables

**street**
*(string) (required)*

Street name as it appears in Monheim's digital waste calendar. Use the exact spelling (including umlauts).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: monheim_de
      args:
        street: Marderstraße
```

## How to get the source argument

Open the [Abfallkalender Monheim am Rhein](https://www.monheim.de/leben-in-monheim/abfall-stadtreinigung/abfallkalender) and select your street from the dropdown; use that exact spelling in the configuration.
