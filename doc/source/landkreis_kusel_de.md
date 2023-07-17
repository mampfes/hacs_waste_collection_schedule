# Landkreis Kusel

Support for schedules provided by [Landkreis Kusel](https://www.landkreis-kusel.de/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: landkreis_kusel_de
      args:
        ortsgemeinde: ORTSGEMEINDE
        
```

### Configuration Variables

**ortsgemeinde**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: landkreis_kusel_de
      args:
        ortsgemeinde: Adenbach
        
```

## How to get the source argument

Go to <https://www.landkreis-kusel.de/buergerservice-und-verwaltung/themen/abfallwirtschaft/abfall-app-abfallkalender/> and select your `Ortsgemeinde` and use this as `ortsgemeinde` parameter. Copy it exactly from the web page.
