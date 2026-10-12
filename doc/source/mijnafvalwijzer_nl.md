# Afval Wijzer

Support for schedules provided by [Afval Wijzer](https://www.mijnafvalwijzer.nl).

Source for all cities regions supported in mijnafvalwijzer.nl

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mijnafvalwijzer_nl
      args:
        postcode: POSTCODE
        number: NUMBER
        add: ADD
```

### Configuration Variables

**postcode**  
*(string) (required)*

**number**  
*(string) (required)*

**add**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mijnafvalwijzer_nl
      args:
        postcode: 5651AN
        number: '34'
        add: A
```

## How to get the source arguments

Enter the same postcode, house number and (optional) addition as for your home address at https://www.mijnafvalwijzer.nl/
