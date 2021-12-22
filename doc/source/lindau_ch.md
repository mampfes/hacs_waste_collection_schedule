# Abfallwirtschaft Zollernalbkreis

Support for schedules provided by [https://www.lindau.ch/abfalldaten](https://www.lindau.ch/abfalldaten).



## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lindau_ch
      args:
        city: Tagelswangen
        types:
          - "kehricht"
          - "grungut"
          - "papier und karton"
          - "altmetalle" 
          - "hackseldienst"
```

### Configuration Variables

**city**<br>
*(string) (required)* <br>
One of <br>
Names: Grafstal, Lindau, Tagelswangen, Winterberg <br>
or ID: 190, 192, 193, 191

**types**<br>
*(list of string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lindau_ch
      args:
        city: Tagelswangen
        types:
          - "kehricht"
          - "grungut"
          - "papier und karton"
          - "altmetalle" 
          - "hackseldienst"
```

## How to get the source arguments




