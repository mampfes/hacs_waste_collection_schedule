# Zweckverband Abfallwirtschaft Region Hannover

Support for schedules provided by [Zweckverband Abfallwirtschaft Region Hannover](https://www.aha-region.de/), serving the region around Hannover, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: aha_region_de
      args:
        gemeinde: Gemeinde
        strasse: Straße
        hnr: Hausnummer
        zusatz: Adresszusatz
        
```

### Configuration Variables

**gemeinde**  
*(String) (required)*

**strasse**  
*(String) (required)*

**hnr**  
*(String | Integer) (required)*

**zusatz**  
*(String | Integer) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: aha_region_de
      args:
        gemeinde: Neustadt a. Rbge.
        strasse: Am Rotdorn / Nöpke
        hnr: "1"
        zusatz: ""
        
```

## How to get the source argument

Find the parameter of your address using [https://www.aha-region.de/abholtermine/abfuhrkalen](https://www.aha-region.de/abholtermine/abfuhrkalen) and write them exactly like on the web page.
