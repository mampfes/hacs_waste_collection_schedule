# Abfallbehandlungsgesellschaft Havelland mbH

Support for schedules provided by [Abfallbehandlungsgesellschaft Havelland mbH](https://abfall-havelland.de/), serving Havelland, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: abfall_havelland_de
      args:
        ort: ORT
        strasse: STRAßE
        
```

### Configuration Variables

**ort**  
*(String) (required)*

**strasse**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: abfall_havelland_de
      args:
        ort: Wustermark
        strasse: Drosselgasse
        
```

## How to get the source argument

Find the parameter of your address using [https://www.abfall-havelland.de/index.php?page_id=543](https://www.abfall-havelland.de/index.php?page_id=543) and write them exactly like on the web page.
