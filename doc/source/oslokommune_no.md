# Oslo Kommune

Support for schedules provided by [Oslo Kommune](https://www.oslo.kommune.no).

Oslo Kommune (Norway).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: oslokommune_no
      args:
        street_name: STREET_NAME
        house_number: HOUSE_NUMBER
        house_letter: HOUSE_LETTER
        street_id: STREET_ID
        point_id: POINT_ID
```

### Configuration Variables

**street_name**  
*(string) (required)*

**house_number**  
*(string) (required)*

**house_letter**  
*(string) (optional)*

**street_id**  
*(string) (required)*

**point_id**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: oslokommune_no
      args:
        street_name: Olaf Ryes Plass
        house_number: 8
        house_letter: ''
        street_id: 15331
```

## How to get the source arguments

street_id is the address code (adressekode) of the street. Find it with https://ws.geonorge.no/adresser/v1/sok?sok=Min%20Gate%2012 (the adressekode field). point_id is optional: set it to a waste point Id from the oslo.kommune.no response to show only that collection point.
