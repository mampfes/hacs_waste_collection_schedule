# TAMAX (Gmina Sędziszów)

Support for schedules provided by [TAMAX (Gmina Sędziszów)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Miasto i Gmina Sędziszów.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_sedziszow_pl
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
    - name: tamax_sedziszow_pl
      args:
        area: "S\u0119dzisz\xF3w: Akacjowa, Batalion\xF3w Ch\u0142opskich, B\u0105kowska,\
          \ Bohater\xF3w Swaryszowa\u2026"
```

## How to get the source arguments

Open Gmina Sędziszów (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/swietokrzyskie/gmina-sedziszow/ and the JEDNORODZINNE (single-family housing) calendar. Select the village group or street list your address appears in; street choices show the beginning of each list, read the PDF for the complete streets. The current half-year calendar is found on the page each time, so a new upload is picked up without a change. Apartment blocks, housing communities and businesses have separate calendars that are not supported.
