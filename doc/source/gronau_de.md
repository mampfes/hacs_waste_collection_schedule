# Gronau

Support for schedules provided by [Gronau](https://abfallkalender.regioit.de/kalender-wml/).

Source for Abfallkalender Gronau, Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gronau_de
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
    - name: gronau_de
      args:
        street: "Viktoriastra\xDFe"
```

## How to get the source arguments

Open https://abfallkalender.regioit.de/kalender-wml/index.jsp?ort=Gronau and pick your street; use the exact spelling shown there.
