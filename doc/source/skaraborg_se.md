# Avfall & Återvinning Skaraborg

This is a waste collection schedule integration for Avfall & Återvinning Skaraborg in Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: skaraborg_se
      args:
        address: ADDRESS
        city: CITY
```

### Configuration Variables

**address**
*(string) (required)*

**city**
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: skaraborg_se
      args:
        address: Eric Ugglas Plats 2
        city: Skövde
```

## How to get the correct address

Visit [Se tömningsdagar för sophämtning](https://avfallskaraborg.se/sophamtning/se-tomningsdagar-for-sophamtning) and follow the instructions on the page.
Both address and city is case-sensitive, so copy the values carefully.