# Abfallwirtschaft Landkreis Harburg

Support for schedules provided by [Abfallwirtschaft Landkreis Harburg](https://www.landkreis-harburg.de).

Abfallwirtschaft Landkreis Harburg

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
*(string) (optional)*

**level_2**  
*(string) (optional)*

**level_3**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aw_harburg_de
      args:
        level_1: Hanstedt
        level_2: Evendorf
```
