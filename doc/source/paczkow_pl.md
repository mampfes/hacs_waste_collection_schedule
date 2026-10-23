# Gmina Paczków

Support for schedules provided by [Gmina Paczków](https://paczkow.pl).

Source for Gmina Paczków, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: paczkow_pl
      args:
        street: STREET
        multi_family: MULTI_FAMILY
```

### Configuration Variables

**street**  
*(string) (required)*

**multi_family**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: paczkow_pl
      args:
        street: Kopernika
```

## How to get the source arguments

Enter your street (in the town of Paczków) or your village, as printed in the quarterly schedule PDFs on https://paczkow.pl/2442/harmonogram-odbioru-odpadow-komunalnych-na-terenie-gminy-paczkow.html (e.g. 'Kopernika', 'Armii Krajowej' or 'Kamienica'). Accents and case are ignored. Tick 'multi_family' for a multi-family building (budynek wielorodzinny).
