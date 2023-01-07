# Abfalltermine Forchheim

Support for Stadt Fürth schedules provided by [abfallwirtschaft.fuerth.eu](https://www.abfallwirtschaft.fuerth.eu/) located in Bavaria, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfalltermine_fuerth_de
      args:
        city: CITY
        area: AREA
```

### Configuration Variables

**city**  
*(string) (required)*

**area**  
*(string) (required)*

### How to get the source arguments
The arguments can be found on [abfallwirtschaft.fuerth.eu](https://www.abfallwirtschaft.fuerth.eu/).
Search for your area. Use the part in front of the dash as `city` argument and the part behind it as `area` argument. Do not insert additional spaces.

**Examples**
Fürth - Flößaustraße

```yaml
city: Fürth
area: Flößaustraße
```