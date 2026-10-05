# Monheim am Rhein

Support for schedules provided by [Monheim am Rhein](https://www.monheim.de).

Source for Monheim am Rhein waste collection (Stadt Monheim am Rhein, NRW).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: monheim_de
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: monheim_de
      args:
        street: "Marderstra\xDFe"
```

## How to get the source arguments

Open https://www.monheim.de/leben-in-monheim/abfall-stadtreinigung/abfallkalender and pick your street; use the exact spelling shown there.
