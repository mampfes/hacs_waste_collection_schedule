# TAMAX (Gmina Miasto Bochnia)

Support for schedules provided by [TAMAX (Gmina Miasto Bochnia)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Miasto Bochnia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_bochnia_pl
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
    - name: tamax_bochnia_pl
      args:
        area: "Trasa I: Bracka, Bernardy\u0144ska, Plac Czapli\u0144skiego, Solna\u2026"
```

## How to get the source arguments

Open Gmina Miasto Bochnia (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-bochnia/ and the JEDNORODZINNE (single-family housing) calendar, which has one page per route (TRASA). Select the route whose street list contains your street; the choices show the beginning of each list. Ash (POPIÓŁ) is reported as Other; the bulky waste collection also takes electrical equipment and tyres. Apartment blocks (WIELORODZINNE) are only given as weekday rules without dates and are not supported.
