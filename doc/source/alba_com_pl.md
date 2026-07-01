# ALBA Swarzędz

Support for schedules provided by [ALBA Swarzędz](https://www.alba.com.pl/odbior_odpadow_wywoz_smieci/swarzedz).

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
*(string) (required)*

City name in uppercase, e.g. `SWARZĘDZ`.

**street**
*(string) (required)*

Street name in uppercase, e.g. `JÓZEFA RIVOLIEGO`.

**number**
*(string) (required)*

House or building number, e.g. `2`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: alba_com_pl
      args:
        city: SWARZĘDZ
        street: JÓZEFA RIVOLIEGO
        number: "2"
```

## How to get the arguments

Open [https://www.alba.com.pl/odbior_odpadow_wywoz_smieci/swarzedz](https://www.alba.com.pl/odbior_odpadow_wywoz_smieci/swarzedz) and use the schedule search form. Select your city, street and house number from the dropdowns. Use the exact values shown (in uppercase) as the source arguments.
