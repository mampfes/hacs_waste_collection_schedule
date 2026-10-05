# PUP Saubermacher

Support for schedules provided by [PUP Saubermacher](https://www.pup-saubermacher.si/).

Source for PUP Saubermacher.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pup_si
      args:
        place_id: PLACE_ID
```

### Configuration Variables

**place_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pup_si
      args:
        place_id: 412177
```

## How to get the source arguments

Find your place_id (Odjemno mesto number) on your monthly PUP bill, or visit https://www.pup-saubermacher.si/index.php/domov/urnik-odvoza-odpadkov
