# Gmina Pisz

Support for schedules provided by [Gmina Pisz](https://www.pisz.pl).

Source for Gmina Pisz (town of Pisz and its villages), Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pisz_pl
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
        building: BUILDING
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (optional)*

**house_number**  
*(string) (optional)*

**building**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pisz_pl
      args:
        city: Pisz
        street: "Wile\u0144ska"
```

## How to get the source arguments

In the town enter `Pisz`, your street as printed in the schedule (for example `Wileńska` or `Dr. Władysława Klementowskiego`) and whether you live in a house (`jednorodzinna`) or a block of flats (`wielorodzinna`); blocks of flats also need the house number. In a village enter only the village, for example `Rakowo Piskie`. The schedules are attached to the yearly announcement on https://www.pisz.pl/pl/szczegoly-kategorii/69.
