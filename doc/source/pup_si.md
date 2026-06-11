# Simbio

Support for schedules provided by [Simbio](https://www.simbio.si/sl/), serving Simbio, Slovenia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: pup_si
      args:
        place_id: ODJEMNO MESTO (številka)
```

### Configuration Variables

**place_id**  
*(Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: pup_si
      args:
        place_id: 12345
        
```

## How to get the source argument

Find the parameter of your place id written on you monthly bill for PUP. The number is written on the right side of "Odjemno mesto:" row.

For more information follow go to PUP website [https://www.pup-saubermacher.si/index.php/domov/urnik-odvoza-odpadkov](https://www.pup-saubermacher.si/index.php/domov/urnik-odvoza-odpadkov).
