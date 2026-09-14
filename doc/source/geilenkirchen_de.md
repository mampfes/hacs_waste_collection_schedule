# Stadt Geilenkirchen

Support for waste collection schedules provided by the city of [Geilenkirchen](https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/), North Rhine-Westphalia, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: geilenkirchen_de
      args:
        street: Aldenhovener Strasse
```

### Configuration Variables

**street**
*(string) (required)*

The street name as shown on the [collection calendar](https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/), e.g. `Aldenhovener Strasse`.

Note that Geilenkirchen spells its streets with `strasse` rather than `straße`. If the name you enter cannot be found, or matches more than one street, the resulting error message lists the closest matches so you can pick the correct one.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: geilenkirchen_de
      args:
        street: Ahornweg
```

## How to get the source argument

Visit the [collection calendar](https://www.geilenkirchen.de/rathaus/online-dienstleistungen-und-andere-angebote/abfallkalender/) and use the street search box there to find the exact spelling of your street.
