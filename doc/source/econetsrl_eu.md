# Econet

Support for schedules provided by [Econet](https://www.econetsrl.eu).

Source for Econet (Acqui Terme, Ovada and surroundings, Alessandria) door-to-door collection calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: econetsrl_eu
      args:
        comune: COMUNE
        zona: ZONA
```

### Configuration Variables

**comune**  
*(string) (required)*

**zona**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: econetsrl_eu
      args:
        comune: Strevi
```

## How to get the source arguments

Enter your comune as listed on https://www.econetsrl.eu/testi.php?id_testi=25, e.g. `Strevi`. Acqui Terme and Ovada have one calendar per zone: also enter the zone (`Centro Storico`, `Città` or `Standard`); the streets of each zone are listed on the comune's 'Calendari' page. Garden waste (verde) dates are those printed in the calendar, but in most comuni verde is only collected when booked in advance with Econet.
