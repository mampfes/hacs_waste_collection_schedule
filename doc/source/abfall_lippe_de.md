# Abfallwirtschaftsverbandes Lippe

Support for schedules provided by [Abfallwirtschaftsverbandes Lippe](https://abfall-lippe.de), serving Kreis Lippe, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: abfall_lippe_de
      args:
        gemeinde: GEMEINDE
        bezirk: ABFUHRBEZIRK
        
```

### Configuration Variables

**gemeinde**  
*(String) (required)*

**bezirk**  
*(String) (optional)*  
needed if multiple ICS files are offered for your municipality

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: abfall_lippe_de
      args:
        gemeinde: Bad Salzuflen
        bezirk: BB
```

```yaml
waste_collection_schedule:
    sources:
    - name: abfall_lippe_de
      args:
        gemeinde: Barntrup
        bezirk: 3-B
```

```yaml
waste_collection_schedule:
    sources:
    - name: abfall_lippe_de
      args:
        gemeinde: Augustdorf
```

## How to get the source argument

Go to <https://abfall-lippe.de/service/abfuhrkalender/> use your municipal (headline) as `gemeinde` parameter. If your municipality uses your "Abfuhrbezirk" as `bezirk` (spelling must exactly match the characters after "ICS" of the ICS link text)
