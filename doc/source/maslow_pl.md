# Gmina Masłów

Support for schedules provided by [Gmina Masłów](https://www.maslow.pl).

Source for Gmina Masłów, Poland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maslow_pl
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: maslow_pl
      args:
        district: "D\u0105browa, Wi\u015Bni\xF3wka"
```

## How to get the source arguments

Enter your area as named by its schedule link on https://www.maslow.pl/asp/gospodarka-odpadami,66 (in the article 'Harmonogramy odbioru odpadów na <year> rok'), e.g. 'Dąbrowa, Wiśniówka' or 'Zabudowa wielorodzinna'. A single village named in only one link (e.g. 'Wiśniówka') works too.
