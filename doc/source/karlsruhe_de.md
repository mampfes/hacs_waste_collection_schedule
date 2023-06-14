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
        
```

### Configuration Variables

**street**  
*(String) (required)*

**hnr**  
*(String | Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: karlsruhe_de
      args:
        street: Östliche Rheinbrückenstraße
        hnr: 1 
```

## How to get the source argument

Find the parameter of your address using [https://web6.karlsruhe.de/service/abfall/akal/akal.php](https://web6.karlsruhe.de/service/abfall/akal/akal.php) and write them exactly like on the web page.
