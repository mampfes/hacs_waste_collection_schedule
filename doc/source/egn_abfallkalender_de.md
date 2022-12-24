# EGN - Abfallkalender

Support for schedules provided by [egn-abfallkalender.de](https://www.egn-abfallkalender.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: egn_abfallkalender_de
      args:
        city: CITY_NAME
        district: DISTRICT_NAME
        street: STREET_NAME
        housenumber: HOUSE_NUMBER
```

The arguments can be found above the calendar after generating one [here](https://www.egn-abfallkalender.de/kalender#skill-setup-form). Select your city, street and enter your housenumber to show the schedule for your address. The complete information you need are displayed above the calendar view in the format `für <street> <housenumber>, <city> (<district>)`. See also examples below.

### Configuration Variables

**city**  
*(string) (required)*
City, extracted from the displayed address.

**district**  
*(string) (required)*
District, extracted from the displayed address.

**street**  
*(string) (required)*
Street, extracted from the displayed address.

**housenumber**  
*(string) (required)*
Housenumber, extracted from the displayed address.

## Examples

```yaml
# Displayed address: 
# für Albert-Schweitzer-Weg 27, Grevenbroich (Stadtmitte)

waste_collection_schedule:
  sources:
    - name: egn_abfallkalender_de
      args:
        city: Grevenbroich
        district: Stadtmitte
        street: Albert-Schweitzer-Weg
        housenumber: 27
```

```yaml
# Displayed address:
# für Am Damschenpfad 81, Dormagen (Nievenheim)

waste_collection_schedule:
  sources:
    - name: egn_abfallkalender_de
      args:
        city: Dormagen
        district: Nievenheim
        street: "Am Damschenpfad"
        housenumber: 81
```
