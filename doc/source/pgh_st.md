# PGH.ST

Support for schedules provided by [PGH.ST](https://www.pgh.st/), serving the city of Pittsburgh, PA, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pgh_st
      args:
        house_number: HOUSE_NUMBER
        street_name: STREET_NAME
        zipcode: ZIPCODE
```

### Configuration Variables

**house_number**  
*(integer) (required)*

**street_name**  
*(string) (required)*

**zipcode**  
*(integer) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pgh_st
      args:
        house_number: 800
        street_name: Negley
        zipcode: 15232
```

## How to get the source arguments

The source arguments are simply the house mailing address. The street_name field doesn't require cardinal direction (N/S/E/W) or road type (e.g. st) designations, so `S Negley Ave` can just be `Negley`. The zipcode field is just the 5-digit zipcode, not the 9-digit extended zipcode.
