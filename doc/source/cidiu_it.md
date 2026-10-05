# CIDIU S.p.A.

Support for schedules provided by [CIDIU S.p.A.](https://cidiu.it/).

Source for CIDIU waste collection services for the north-west Turin province

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cidiu_it
      args:
        city: CITY
        street: STREET
        street_number: STREET_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cidiu_it
      args:
        city: COLLEGNO
        street: VIA CONDOVE
        street_number: '107'
```

## How to get the source arguments

Enter the town served by CIDIU (e.g. Collegno), the street name without the number, and the street number.
