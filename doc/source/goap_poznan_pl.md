# GOAP Poznań

Support for schedules provided by [GOAP Poznań](https://www.goap.poznan.pl/).

Source for the waste collection calendar of GOAP (Związek Międzygminny Gospodarka Odpadami Aglomeracji Poznańskiej), covering municipalities in the Poznań agglomeration such as Murowana Goślina, Czerwonak, Swarzędz and others.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: goap_poznan_pl
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
        location_type: LOCATION_TYPE
        building_type: BUILDING_TYPE
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**location_type**  
*(string) (optional)*

**building_type**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: goap_poznan_pl
      args:
        city: HUTA PUSTA
        street: HUTA PUSTA
        house_number: '1'
        location_type: Z
        building_type: J
```

## How to get the source arguments

Enter the city, street and house number exactly as the GOAP calendar writes them (usually upper case, e.g. 'MUROWANA GOŚLINA'). For villages without named streets the street is often the same as the city, and a house number may carry a suffix such as '5/A'. Set the location type (Z inhabited, N uninhabited, M mixed, R recreational) and building type (J single-family, W multi-family) only if the address is ambiguous.
