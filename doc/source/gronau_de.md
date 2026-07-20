# Gronau

Source for waste collection in Gronau (Westfalen), Germany, provided by the [Abfallkalender](https://abfallkalender.regioit.de/kalender-wml/index.jsp?ort=Gronau) (RegioIT).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gronau_de
      args:
        street: STREET_NAME
```

### Configuration Variables

**street**
*(string) (required)*

Street name as it appears in the Gronau waste calendar. Use the exact spelling (including umlauts).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gronau_de
      args:
        street: Viktoriastraße
```

## How to get the source argument

Open the [Abfallkalender Gronau](https://abfallkalender.regioit.de/kalender-wml/index.jsp?ort=Gronau) and select your street from the dropdown; use that exact spelling in the configuration.
