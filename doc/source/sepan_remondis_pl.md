# SepanRemondis

Support for schedules provided by [SepanRemondis](https://sepan.remondis.pl/harmonogram/) for cities:
-Poznań
-Objezierze
-Oborniki
-Koziegłowy

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sepan_remondis_pl
      args:
        city: Poznań
        street_name: Święty Marcin
        street_number: 1
```

### Configuration Variables

**city**  
*(string)*

**street_address**  
*(string)*

**street_number**  
*(string)*

All arguments must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sepan_remondis_pl
      args:
        city: Poznań
        street_name: Święty Marcin
        street_number: 1
```

## How to get the source arguments

You have to provide city name (Poznań, Objezierze, Oborniki or Koziegłowy) and then your street name and house number (eg 1 or 7/3).
You can check if your address is covered by SepanRemondis provider at page [SepanRemondis](https://sepan.remondis.pl/harmonogram/)