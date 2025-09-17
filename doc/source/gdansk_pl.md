# Gdańsk

Support for schedules provided by [Czyste Miasto Gdańsk](https://czystemiasto.gdansk.pl/harmonogram-odbioru-odpadow/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gdansk_pl
      args:
        street_name: Aleja Grunwaldzka
        street_number: 137
        housing_type: Zabudowa jednorodzinna
```

### Configuration Variables

**street_address**
*(string) (required)*

**street_number**
*(string)(required)*

**housing_type**
*(string)(required)*
Choose from "Zabudowa jednorodzinna", "Zabudowa wielorodzinna" and "Firmy".

All arguments must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gdansk_pl
      args:
        street_name: Aleja Grunwaldzka
        street_number: 137
        housing_type: Zabudowa jednorodzinna
```

## How to get the source arguments

To avoid mistakes it's best to provide the arguments exactly as shown on the [Czyste Miasto Gdańsk](https://czystemiasto.gdansk.pl/harmonogram-odbioru-odpadow/) website.
