# OZO Ostrava

Support for schedules provided by [OZO Ostrava](https://ozoostrava.cz/), serving Ostrava and nearby municipalities, Czech Republic.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ozoostrava_cz
      args:
        obec: MUNICIPALITY
        obvod: DISTRICT
        ulice: STREET
        cislo: HOUSE_NUMBER
```

### Configuration Variables

**obec**  
*(String) (required)* Municipality name (e.g. "Ostrava")

**obvod**  
*(String) (required)* District name (e.g. "Poruba")

**ulice**  
*(String) (required)* Street name (e.g. "Hlavní třída")

**cislo**  
*(String) (required)* House number (e.g. "583")

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ozoostrava_cz
      args:
        obec: Ostrava
        obvod: Poruba
        ulice: "Hlavní třída"
        cislo: "583"
```

## How to get the source arguments

Visit [https://ozoostrava.cz/svoz](https://ozoostrava.cz/svoz) and select your municipality, district, street, and house number from the dropdowns.
