# City of Karlsruhe

Support for schedules provided by [City of Karlsruhe](https://www.karlsruhe.de/), serving Karlsruhe, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: karlsruhe_de
      args:
        street: STRAßE
        hnr: "HAUSNUMMER"
        ladeort: LADEORT
        
```

### Configuration Variables

**street**  
*(String) (required)*

**hnr**  
*(String | Integer) (required)*

**ladeort**  
*(String | Integer) (optional)*  
only needed for some very limited addresses


## Example


### without `ladeort`

```yaml
waste_collection_schedule:
    sources:
    - name: karlsruhe_de
      args:
        street: Östliche Rheinbrückenstraße
        hnr: 1 
```

```yaml
waste_collection_schedule:
    sources:
    - name: karlsruhe_de
      args:
        street: Bernsteinstraße
        hnr: 10 
        ladeort: 2
```

## How to get the source argument

Find the parameter of your address using [https://web6.karlsruhe.de/service/abfall/akal/akal.php](https://web6.karlsruhe.de/service/abfall/akal/akal.php) and write them exactly like on the web page.

`ladeort` is only required if the website prompts for a "Abholplatz". `ladeort` is the Number of the drop down element behind "Abholplatz" (e.g. 1 for the first element of the drop down menu, 2 for the second item of the drop down menu ...)
