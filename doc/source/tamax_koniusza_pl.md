# TAMAX (Gmina Koniusza)

Support for schedules provided by [TAMAX (Gmina Koniusza)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Koniusza.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_koniusza_pl
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
    - name: tamax_koniusza_pl
      args:
        area: "Muniaczkowice, Chor\u0105\u017Cyce, Dalewice, Rz\u0119dowice, Piotrkowice Wielkie,\
          \ Budziejowice"
```

## How to get the source arguments

Open Gmina Koniusza (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/malopolskie/gmina-koniusza/ and select the village group your village appears in. The current half-year calendar is found on the page each time, so a new upload is picked up without a change. Mixed and bio waste are collected on the same day, as are plastic and paper. Apartment blocks (zabudowa wielorodzinna) are only given as weekly and monthly rules without dates and are not supported.
