# Bydgoszcz Pronatura

Support for schedules provided by [Bydgoszcz Pronatura](http://www.pronatura.bydgoszcz.pl/).

Source for Bydgoszcz city garbage collection by Pronatura

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pronatura_bydgoszcz_pl
      args:
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pronatura_bydgoszcz_pl
      args:
        street_name: LEGNICKA
        street_number: 1
```

## How to get the source arguments

Enter your street name and building number in Bydgoszcz as they appear in the Pronatura schedule. Neither is case-sensitive.
