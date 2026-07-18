# mags Mönchengladbacher Abfall-, Grün- und Straßenbetriebe AöR

Support for schedules provided by [mags Mönchengladbacher Abfall-, Grün- und Straßenbetriebe AöR](https://mags.de).

Source for Stadt Mönchengladbach

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mags_de
      args:
        street: STREET
        number: NUMBER
        turnus: TURNUS
```

### Configuration Variables

**street**  
*(string) (required)*

**number**  
*(string) (required)*

**turnus**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mags_de
      args:
        street: Schlossacker
        number: 43
        turnus: 2
```
