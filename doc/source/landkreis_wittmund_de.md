# Landkreis-Wittmund.de

Support for schedules provided by [Landkreis-Wittmund.de](https://www.landkreis-wittmund.de) located in Lower Saxony, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_wittmund_de
      args:
        city: Werdum
        # optional
        # street: street name
```

### Configuration Variables

**city**<br>
*(string) (required)*

**street**<br>
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_wittmund_de
      args:
        city: Werdum
```

Use `sources.customize` to filter or rename the waste types:

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_wittmund_de
      args:
        city: Werdum
      calendar_title: Abfallkalender
      customize:
        # rename types to shorter name
        - type: Restmülltonne
          alias: Restmüll
        
        # hide unwanted types
        - type: Baum- und Strauchschnitt
          show: false
```
