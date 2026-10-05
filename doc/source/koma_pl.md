# KOMA

Support for schedules provided by [KOMA](https://koma.pl).

Source for KOMA waste collection (e.g. Nowy Dwór Gdański, Poland).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: koma_pl
      args:
        gmina: GMINA
        miejscowosc: MIEJSCOWOSC
        ulica: ULICA
        numer_domu: NUMER_DOMU
```

### Configuration Variables

**gmina**  
*(string) (required)*

**miejscowosc**  
*(string) (required)*

**ulica**  
*(string) (optional)*

**numer_domu**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: koma_pl
      args:
        gmina: "Nowy Dw\xF3r Gda\u0144ski"
        miejscowosc: "Nowy Dw\xF3r Gda\u0144ski"
        ulica: "Kana\u0142owa"
        numer_domu: '5'
```

## How to get the source arguments

Open https://koma.pl/harmonogram-odpadow/ and step through the dropdowns (Wybierz Miasto -> miejscowość -> ulica -> numer domu) to find the exact spelling of your commune (gmina), town, street and house number. Leave the street empty for towns without streets.
