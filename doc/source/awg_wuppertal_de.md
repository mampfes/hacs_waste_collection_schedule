# AWG Wuppertal

Support for schedules provided by [AWG Wuppertal](https://awg-wuppertal.de/), serving Wuppertal, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: awg_wuppertal_de
      args:
        street: STREET (Straße)
        
```

### Configuration Variables

**street**  
*(String) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: awg_wuppertal_de
      args:
        street: Hauptstraße
        
```

## How to get the source argument

Find the parameter of your address using [https://awg-wuppertal.de/privatkunden/abfallkalender.html](https://awg-wuppertal.de/privatkunden/abfallkalender.html) and write them exactly like on the web page.
