# Abfallwirtschaft Stadt Schweinfurt

Support for schedules provided by [Abfallwirtschaft Stadt Schweinfurt](https://www.schweinfurt.de).

Source for Schweinfurt, Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: schweinfurt_de
      args:
        address: ADDRESS
        showmobile: SHOWMOBILE
```

### Configuration Variables

**address**  
*(string) (required)*

**showmobile**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: schweinfurt_de
      args:
        address: Ahornstrasse
```

## How to get the source arguments

Enter the street name as listed in the street dropdown at https://www.schweinfurt.de (e.g. 'Ahornstrasse'). Enable 'showmobile' to also include the mobile recycling center (Mobiler Wertstoffhof) dates.
