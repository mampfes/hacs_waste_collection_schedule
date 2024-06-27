# Poznań

Support for schedules provided by [Poznań](https://poznan.pl).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: poznan_pl
      args:
        street_name: Święty Marcin
        street_number: 1
```

### Configuration Variables

**street_address**  
*(string) (required)*

**street_number**  
*(string)(required)*

All arguments must be provided.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: poznan_pl
      args:
        street_name: Święty Marcin
        street_number: 1
```

## How to get the source arguments

You have to provide your street name and house number (eg 1 or 7/3).
You can check if your address is covered by SepanRemondis provider at page [poznan.pl](https://www.poznan.pl/mim/odpady/harmonogramy.html)
