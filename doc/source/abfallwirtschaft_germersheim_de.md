# Abfalltermine Landkreis Germersheim

Support for Landkreis Germersheim schedules provided by [abfalltermine-forchheim.de](https://www.abfallwirtschaft-germersheim.de/) located in Rhineland-Palatinate, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_germersheim_de
      args:
        city: City
        street: Street
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (optional)*

### How to get the source arguments
The arguments can be found on [abfall-termine abfallwirtschaft-germersheim.de](https://www.abfallwirtschaft-germersheim.de/online-service/abfall-termine/abfalltermine-ics-export-bis-240-liter.html).
select your city and street and use them as the arguments, make sure they are spelled exactly like on the web Page. (If there is no street you can leave it empty)

**Examples**
Bellheim - Albert-Schweitzer-Str.

```yaml
city: Bellheim
street: Albert-Schweitzer-Str.
```

Dormitz - Dormitz

```yaml
city: Hatzenbühl
```
