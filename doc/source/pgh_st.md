# City of Pittsburgh

Support for schedules provided by [City of Pittsburgh](https://www.pgh.st).

Source for PGH.ST services for the city of Pittsburgh, PA, USA.

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
*(string) (required)*

**street_name**  
*(string) (required)*

**zipcode**  
*(string) (required)*

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
