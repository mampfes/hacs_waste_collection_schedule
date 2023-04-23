# AWB Abfallwirtschaft Vechta

Support for schedules provided by [AWB Abfallwirtschaft Vechta](https://www.abfallwirtschaft-vechta.de/), serving Landkreis Vechta, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: abfallwirtschaft_vechta_de
      args:
        stadt: STADT
        strasse: STRASSE
        
```

### Configuration Variables

**stadt**  
*(String) (required)*

**strasse**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: abfallwirtschaft_vechta_de
      args:
        stadt: Vechta
        strasse: An der Hasenweide
        
```

## How to get the source argument

Find the parameter of your address using [https://www.abfallwirtschaft-vechta.de/index.php/termine/abfuhrkalender](https://www.abfallwirtschaft-vechta.de/index.php/termine/abfuhrkalender) and write them exactly like on the web page.

## Filtering

This source returns multiple paper pickup types you probably want only one of them detailed information [Configuring Source(s)](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/doc/installation.md#configuring-sources)

### Filtering Example

hiding `Siemer Altpapier`

```yaml
waste_collection_schedule:
    sources:
    - name: abfallwirtschaft_vechta_de
      args:
        stadt: Vechta
        strasse: An der Hasenweide
      customize:
        - type: Altpapier 1 Siemer
          show: false
        - type: Altpapier 2 Siemer
          show: false
        
```
