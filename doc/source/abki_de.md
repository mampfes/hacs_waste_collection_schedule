# Abfallwirtschaftsbetrieb Kiel (ABK)

Support for schedules provided by [Abfallwirtschaftsbetrieb Kiel (ABK)](https://abki.de/).

Source for Abfallwirtschaftsbetrieb Kiel (ABK).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abki_de
      args:
        street: STREET
        number: NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abki_de
      args:
        street: "auguste-viktoria-stra\xDFe"
        number: 14
```
