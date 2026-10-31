# TAMAX (Gmina Książ Wielki)

Support for schedules provided by [TAMAX (Gmina Książ Wielki)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Książ Wielki.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_ksiaz_wielki_pl
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
    - name: tamax_ksiaz_wielki_pl
      args:
        area: "Ksi\u0105\u017C Wielki, Wielka Wie\u015B"
```

## How to get the source arguments

Open Gmina Książ Wielki (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-ksiaz-wielki/ and select the village group your village appears in. The current half-year calendar is found on the page each time, so a new upload is picked up without a change. Mixed waste is collected together with either the segregated waste or the bio waste; the bulky waste collection also takes car tyres and textiles. Apartment blocks (BLOKI) are only given as weekday rules without dates and are not supported.
