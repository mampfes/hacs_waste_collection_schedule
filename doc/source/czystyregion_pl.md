# Czysty Region

Support for waste collection schedules provided by [Związek Międzygminny Czysty Region](https://www.czystyregion.pl) via its schedule lookup at [czystyregion.pl/Harmonogramy](https://www.czystyregion.pl/Harmonogramy) (Opole/Silesia region, Poland — covering the communes Cisek, Dobrodzień, Gogolin, Izbicko, Kędzierzyn-Koźle, Kolonowskie, Leśnica, Pawłowiczki, Polska Cerekiew, Reńska Wieś, Tarnów Opolski, Ujazd, Walce, Zdzieszowice and Zawadzkie).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: czystyregion_pl
      args:
        gmina: Cisek
        miejscowosc: Cisek
        rodzaj: jednorodzinna
```

If the town/village has several separate schedule areas (typically larger towns split into street-based "Rejon" groups), also pass a distinctive street name to disambiguate:

```yaml
waste_collection_schedule:
  sources:
    - name: czystyregion_pl
      args:
        gmina: Kędzierzyn-Koźle
        miejscowosc: Kędzierzyn-Koźle
        rodzaj: wielorodzinna
        ulica: Piastów
```

### Configuration Variables

**gmina**  
*(string) (required)*

Name of the commune (gmina) as listed on czystyregion.pl.

**miejscowosc**  
*(string) (required)*

Name of the town/village as listed on czystyregion.pl.

**rodzaj**  
*(string) (required)*

One of: `wielorodzinna` (multi-family building), `jednorodzinna` (single-family house), `firma` (business/institution).

**ulica**  
*(string) (optional)*

Street name used to pick the right area when your town has several separate schedules. Only needed if the source reports an ambiguous result; the error message will list the available areas to choose from.

## How to get the source arguments

Open [czystyregion.pl/Harmonogramy](https://www.czystyregion.pl/Harmonogramy) and step through the dropdowns (Wybierz gminę → Wybierz rodzaj → Wybierz miejscowość) to find the exact spelling of your commune (gmina) and town/village (miejscowość). If the result table lists more than one row for your town (e.g. large towns split into several "Rejon" street groups), also note a distinctive street name from the "Rejon" description shown for your area and pass it as `ulica`.
