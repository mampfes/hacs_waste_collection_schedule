# KWB-Goslar.de

Support for schedules provided by [KWB-Goslar.de](https://www.kwb-goslar.de/Abfallwirtschaft/Abfuhr/) located in Lower Saxony, Germany.  

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kwb_goslar_de
      args:
        pois: 2523.602 # Berliner Straße (Clausthal-Zellerfeld)
```

### Configuration Variables

**pois**
*(string) (required)*

#### How to find the `pois` value

1. Open [Online-Abfuhrkalender 2022](https://www.kwb-goslar.de/Abfallwirtschaft/Abfuhr/Online-Abfuhrkalender-2022/) (`Abfallwirtschaft -> Abfuhr -> Online-Abfuhrkalender 2022`)
2. Select your city (`Ort auswählen`)
3. Select your district/street (`Ortsteil, Straße auswählen`)
4. Copy the `pois` value out of the url (e.g. `https://www.kwb-goslar.de/Abfallwirtschaft/Abfuhr/Online-Abfuhrkalender-2022/index.php?ModID=48&...&pois=2523.602`)

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kwb_goslar_de
      args:
        pois: 2523.409 # Braunschweiger Straße (Seesen)
```

Use `sources.customize` to filter or rename the waste types:

```yaml
waste_collection_schedule:
  sources:
    - name: kwb_goslar_de
      args:
        pois: 2523.409 # Braunschweiger Straße (Seesen)
      calendar_title: Abfuhrtermine - Braunschweiger Straße (Seesen)
      customize:
        # rename types to shorter name
        - type: Restmülltonne
          alias: Restmüll
        
        # hide unwanted types
        - type: Baum- und Strauchschnitt
          show: false
```
