# Irado

Support for schedules provided by [Irado](https://www.irado.nl).

Source for Irado waste collection services, covering Vlaardingen, Schiedam, Maassluis, Capelle aan den IJssel and Voorne aan Zee (Netherlands).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: irado_nl
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
        suffix: SUFFIX
```

### Configuration Variables

**postcode**  
*(string) (required)*

**house_number**  
*(string) (required)*

**suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: irado_nl
      args:
        postcode: 3136GZ
        house_number: '7'
```

## How to get the source arguments

Enter the postcode (e.g. 3131VX) and house number you would use at https://www.irado.nl/afvalkalender
