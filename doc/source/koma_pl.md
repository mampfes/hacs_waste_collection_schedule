# KOMA

Support for waste collection schedules provided by [KOMA](https://koma.pl) via its address lookup at [koma.pl/harmonogram-odpadow](https://koma.pl/harmonogram-odpadow/) (e.g. Nowy Dwór Gdański, Poland).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: koma_pl
      args:
        gmina: Nowy Dwór Gdański
        miejscowosc: Nowy Dwór Gdański
        ulica: Kanałowa
        numer_domu: "5"
```

### Configuration Variables

**gmina**  
*(string) (required)*

Name of the commune (gmina) as listed on koma.pl.

**miejscowosc**  
*(string) (required)*

Name of the town/village.

**numer_domu**  
*(string) (required)*

House number.

**ulica**  
*(string) (optional)*

Street name. Leave empty for towns without streets.

## How to get the source arguments

Open [koma.pl/harmonogram-odpadow](https://koma.pl/harmonogram-odpadow/) and step through the dropdowns (Wybierz Miasto → miejscowość → ulica → numer domu) to find the exact spelling of your gmina, town, street and house number.
