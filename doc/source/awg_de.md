# ZAW Donau-Wald

Support for schedules provided by [ZAW Donau-Wald](https://www.awg.de/), serving Regen, Deggendorf, Freyung-Grafenau, Passau, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: awg_de
      args:
        city: CITY (Ort)
        street: STREET (Straße)
        hnr: "HOUSE NUMBER (Hausnummer)"
        addition: ADDITION (Hausnummerzusatz)
        
```

### Configuration Variables

**city**  
*(String) (required)*

**street**  
*(String) (required)*

**hnr**  
*(String) (required)*

**addition**  
*(String) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: awg_de
      args:
        city: Achslach
        street: Aign
        hnr: "1"        
```

```yaml
waste_collection_schedule:
    sources:
    - name: awg_de
      args:
        city: Böbrach
        street: Bärnerauweg
        hnr: 10
        addition: "A"      
```

## How to get the source argument

Find the parameter of your address using [https://www.awg.de/abfallentsorgung/abfuhrkalender](https://www.awg.de/abfallentsorgung/abfuhrkalender) and write them exactly like on the web page.
