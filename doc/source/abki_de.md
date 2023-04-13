# Abfallwirtschaftsbetrieb Kiel (ABK)

Support for schedules provided by [Abfallwirtschaftsbetrieb Kiel (ABK)](https://abki.de/), serving Kiel, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: abki_de
      args:
        street: STREET
        number: "HOUSE NUMBER"
        
```

### Configuration Variables

**street**  
*(String) (required)*

**number**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: abki_de
      args:
        street: Achterwehrer Straße
        number: 1 a
        
```

## How to get the source argument

Find the parameter of your address using [https://abki.de/dienste/entsorgung-und-recycling/behälter/leerungstermine.html](https://abki.de/dienste/entsorgung-und-recycling/behälter/leerungstermine.html) and write them exactly like on the web page.
