# TAMAX (Miasto Wieliczka)

Support for schedules provided by [TAMAX (Miasto Wieliczka)](https://www.tamax.net.pl).

Source for TAMAX household mixed and bio waste collection in Miasto Wieliczka.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_wieliczka_pl
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_wieliczka_pl
      args:
        area: "Rejon I: Bednarka, Czarnochowska, Dani\u0142owicza, Deskura\u2026"
```

## How to get the source arguments

Open https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-wieliczka/ and select the district (REJON) whose PDF lists your street; the choices show the beginning of each street list. These district calendars list only the mixed and bio waste dates; other fractions are not printed in them and are not included.
