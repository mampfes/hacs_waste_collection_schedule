# AW Harburg

Support for schedules provided by [AW Landkreis Harburg](https://www.landkreis-harburg.de) located in Lower Saxony, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aw_harburg
      args:
          district_level_1: "Hanstedt"
          district_level_2: "Evendorf"
```

### Configuration Variables

**district_level_1**<br>
*(string) (required)*

**district_level_2**<br>
*(string) (required)*

**district_level_3**<br>
*(string) (optional - depending on district_level_2)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aw_harburg
      args:
          district_level_1: "Buchholz"
          district_level_2: "Buchholz mit Steinbeck (ohne Reindorf)"
          district_level_3: "Seppenser Mühlenweg Haus-Nr. 1 / 2"
      customize:
        - type: Biotonne
          alias: Biomüll
          show: true
        - type: Grünabfall
          alias: Grünabfall
          show: true
        - type: Gelber Sack
          alias: Gelber Sack
          show: true
        - type: Hausmüll 14-täglich
          alias: Hausmüll 2wö
          show: true
        - type: Hausmüll 4-wöchentlich
          alias: Hausmüll 4wö
          show: true
        - type: Altpapier
          alias: Papier
          show: true
```

Use `sources.customize` to filter or rename the waste types:

```yaml
waste_collection_schedule:
  sources:
    - name: aw_harburg
      args:
          district_level_1: "Buchholz"
          district_level_2: "Buchholz mit Steinbeck (ohne Reindorf)"
          district_level_3: "Seppenser Mühlenweg Haus-Nr. 1 / 2"
      customize:
        - type: Biotonne
          alias: Biomüll
          show: true
        - type: Grünabfall
          alias: Grünabfall
          show: true
        - type: Gelber Sack
          alias: Gelber Sack
          show: true
        - type: Hausmüll 14-täglich
          alias: Hausmüll 2wö
          show: true
        - type: Hausmüll 4-wöchentlich
          alias: Hausmüll 4wö
          show: true
        - type: Altpapier
          alias: Papier
          show: true

sensor:
  # Nächste Müllabholung
  - platform: waste_collection_schedule
    name: Nächste Leerung

  # Nächste Biomüll Leerung
  - platform: waste_collection_schedule
    name: Nächste Biomüll Leerung
    types: Biomüll

  # Nächste Grünabfall Abholung
  - platform: waste_collection_schedule
    name: Nächste Grünabfall Abholung
    types: Grünabfall

  # Nächste Gelber Sack Abholung
  - platform: waste_collection_schedule
    name: Nächste Gelber Sack Abholung
    types: Gelber Sack

  # Nächste Hausmüll 14-täglich Leerung
  - platform: waste_collection_schedule
    name: Nächste Hausmüll 2wö Leerung
    types: Hausmüll 2wö

  # Nächste Hausmüll 4-wöchentlich Leerung
  - platform: waste_collection_schedule
    name: Nächste Hausmüll 4wö Leerung
    types: Hausmüll 4wö

  # Nächste Papier Leerung
  - platform: waste_collection_schedule
    name: Nächste Papier Leerung
    types: Papier
```

## How to get the source arguments

Check [AW Harburg Abfallkalender](https://www.landkreis-harburg.de/bauen-umwelt/abfallwirtschaft/abfallkalender/) if you need two or three levels of entries in the config. The strings need to be written in the exact same way as in the webinterface e.g. "Bremer Straße Haus-Nr. 93 - 197 / 78 - 158"