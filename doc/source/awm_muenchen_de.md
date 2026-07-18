# AWM München

Support for schedules provided by [AWM München](https://www.awm-muenchen.de).

Source for AWM München.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        r_location_id: R_LOCATION_ID
        b_location_id: B_LOCATION_ID
        p_location_id: P_LOCATION_ID
        r_collection_cycle_string: R_COLLECTION_CYCLE_STRING
        b_collection_cycle_string: B_COLLECTION_CYCLE_STRING
        p_collection_cycle_string: P_COLLECTION_CYCLE_STRING
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**r_location_id**  
*(string) (optional)*

**b_location_id**  
*(string) (optional)*

**p_location_id**  
*(string) (optional)*

**r_collection_cycle_string**  
*(string) (optional)*

**b_collection_cycle_string**  
*(string) (optional)*

**p_collection_cycle_string**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awm_muenchen_de
      args:
        street: Waltenbergerstr.
        house_number: '1'
```

## How to get the source arguments

Fill in the street and house number, then submit. If the address has more than one container location or emptying cycle per waste stream, the fetch error lists the valid values to enter for the corresponding *_location_id / *_collection_cycle_string argument.
