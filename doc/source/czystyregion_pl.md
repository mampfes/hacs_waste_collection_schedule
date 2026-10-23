# Czysty Region

Support for schedules provided by [Czysty Region](https://www.czystyregion.pl).

Source for Związek Międzygminny Czysty Region waste collection (Opole/Silesia region, Poland).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: czystyregion_pl
      args:
        gmina: GMINA
        miejscowosc: MIEJSCOWOSC
        rodzaj: RODZAJ
        ulica: ULICA
```

### Configuration Variables

**gmina**  
*(string) (required)*

**miejscowosc**  
*(string) (required)*

**rodzaj**  
*(string) (required)*

**ulica**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: czystyregion_pl
      args:
        gmina: Cisek
        miejscowosc: Cisek
        rodzaj: jednorodzinna
```

## How to get the source arguments

Open https://www.czystyregion.pl/Harmonogramy and step through the dropdowns (Wybierz gminę -> Wybierz rodzaj -> Wybierz miejscowość) to find the exact spelling of your commune (gmina) and town/village (miejscowość). If the result table lists more than one row for your town (e.g. large towns split into several 'Rejon' street groups), also note a distinctive street name from the 'Rejon' description shown for your area and pass it as 'ulica'.
