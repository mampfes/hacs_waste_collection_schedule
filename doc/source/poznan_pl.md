# Poznań

Support for schedules provided by [Poznań](https://www.poznan.pl/mim/odpady).

Source for Poznań city garbage collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: poznan_pl
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
    - name: poznan_pl
      args:
        street_name: "\u015AWI\u0118TY MARCIN"
        street_number: '2'
```

## How to get the source arguments

Enter the street name and building number exactly as offered on https://www.poznan.pl/mim/odpady/harmonogramy.html.
