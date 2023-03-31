# Potsdam

Support for schedules provided by [Potsdam](https://www.potsdam.de), serving Potsdam, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: potsdam_de
      args:
        ortsteil: ORTSTEIL
        strasse: STRAßE
        
```

### Configuration Variables

**ortsteil**  
*(String) (required)*
**strasse**  
*(String) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: potsdam_de
      args:
        ortsteil: Golm
        strasse: Akazienweg
        
```

## How to get the source argument

Find the parameter of your address using [https://www.potsdam.de/abfallkalender-fuer-potsdam](https://www.potsdam.de/abfallkalender-fuer-potsdam) and write them exactly like on the web page.
