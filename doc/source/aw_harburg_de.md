# AW Harburg

Support for schedules provided by [AW Landkreis Harburg](https://www.landkreis-harburg.de) located in Lower Saxony, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aw_harburg_de
      args:
          level_1: LEVEL_1
          level_2: LEVEL_2
          level_3: LEVEL_3
```

### Configuration Variables

**level_1**  
*(string) (required)*

**level_2**  
*(string) (required)*

**level_3**  
*(string) (optional - depending on level_2)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aw_harburg_de
      args:
          level_1: "Hanstedt"
          level_2: "Evendorf"
```

```yaml
waste_collection_schedule:
  sources:
    - name: aw_harburg_de
      args:
          level_1: "Buchholz"
          level_2: "Buchholz mit Steinbeck (ohne Reindorf)"
          level_3: "Seppenser Mühlenweg Haus-Nr. 1 / 2"
```

## How to get the source arguments

Check [AW Harburg Abfallkalender](https://www.landkreis-harburg.de/bauen-umwelt/abfallwirtschaft/abfallkalender/) if you need two or three levels of entries in the config. The strings need to be written in the exact same way as in the webinterface e.g. "Bremer Straße Haus-Nr. 93 - 197 / 78 - 158".
