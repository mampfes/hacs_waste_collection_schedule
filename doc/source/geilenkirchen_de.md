# Stadt Geilenkirchen

Support for schedules provided by [Stadt Geilenkirchen](https://www.geilenkirchen.de).

Source for the waste collection calendar of the city of Geilenkirchen, North Rhine-Westphalia, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: geilenkirchen_de
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: geilenkirchen_de
      args:
        street: Aldenhovener Strasse
```

## How to get the source arguments

Visit the collection calendar at https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/ and use the street search box there to find the exact spelling of your street (streets are spelled with 'strasse', not 'straße'). Use that exact name as the 'street' argument. If the name you enter cannot be found, or matches more than one street, the resulting error message lists the closest matches.
