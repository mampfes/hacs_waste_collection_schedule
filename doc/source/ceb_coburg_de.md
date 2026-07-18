# Coburg Entsorgungs- und Baubetrieb CEB

Support for schedules provided by [Coburg Entsorgungs- und Baubetrieb CEB](https://www.ceb-coburg.de/).

Source for Coburg Entsorgungs- und Baubetrieb CEB.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ceb_coburg_de
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
    - name: ceb_coburg_de
      args:
        street: "Kanalstra\xDFe, Seite HUK"
```
