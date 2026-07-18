# ALBA Swarzędz

Support for schedules provided by [ALBA Swarzędz](https://www.alba.com.pl).

Source for ALBA waste collection in Swarzędz municipality, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: alba_com_pl
      args:
        city: CITY
        street: STREET
        number: NUMBER
```

### Configuration Variables

**city**  
*(string) (optional)*

**street**  
*(string) (optional)*

**number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: alba_com_pl
      args:
        city: BOGUCIN
        street: BOCZNA
        number: '7'
```

## How to get the source arguments

Open https://www.alba.com.pl/odbior_odpadow_wywoz_smieci/swarzedz and use the schedule search form. Select your city, street and house number from the dropdowns and use those exact values (uppercase) as the source arguments.
