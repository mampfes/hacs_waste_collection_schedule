# Łódź

Support for schedules provided by [Łódź](https://kartalodzianina.pl).

Source for Łódź city garbage collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lodz_pl
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        building_type: BUILDING_TYPE
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**building_type**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lodz_pl
      args:
        street: "Podchor\u0105\u017Cych"
        house_number: '1'
        building_type: '3'
```

## How to get the source arguments

Enter the street name and house number as on kartalodzianina.pl (e.g. 'Piotrkowska' and '104'). building_type is 1 for a single-family house (default), 2 for a multi-family building or 3 for a summer house.
