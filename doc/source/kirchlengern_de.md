# Gemeinde Kirchlengern

Support for waste collection schedules provided by [Gemeinde Kirchlengern](https://www.kirchlengern.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kirchlengern_de
      args:
        strasse: STRASSE
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name, spelled exactly as it appears in the municipality's waste calendar tool (case-insensitive).

## How to find your `strasse`

1. Open the waste calendar on the Kirchlengern website: [Bürgerservice → Abfallkalender/Abfallberatung](https://www.kirchlengern.de/Bürgerservice/Abfallkalender-Abfallberatung/index.php?ffmod=abf).
2. Note your street name from the street drop-down list.
3. Use that street name as the `strasse` argument (e.g. `Alter Postweg`).

If the street cannot be found, the configuration error lists all valid street names as suggestions.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kirchlengern_de
      args:
        strasse: "Alter Postweg"
```

## Bin types returned

| Provider description                     | Returned type                            | Icon                    |
|------------------------------------------|------------------------------------------|-------------------------|
| Restmüll grauer Deckel (2-wöchentlich)   | Restmüll grauer Deckel (2-wöchentlich)   | `Icons.GENERAL_WASTE`   |
| Restmüll blauer Deckel (4-wöchentlich)   | Restmüll blauer Deckel (4-wöchentlich)   | `Icons.GENERAL_WASTE`   |
| Restmüll gelber Deckel (4-wöchentlich)   | Restmüll gelber Deckel (4-wöchentlich)   | `Icons.GENERAL_WASTE`   |
| Biotonne (braune Tonne)                  | Biotonne (braune Tonne)                  | `Icons.BIO_KITCHEN`     |
| Papier (grüne Tonne)                     | Papier (grüne Tonne)                     | `Icons.PAPER`           |
| Gelbe Säcke                              | Gelbe Säcke                              | `Icons.PLASTIC_PACKAGING` |
| Elektroschrott                           | Elektroschrott                           | `Icons.ELECTRONICS`     |
| Sondermüll                               | Sondermüll                               | `Icons.HAZARDOUS`       |
| Sperrmüll und Baumschnitt                | Sperrmüll und Baumschnitt                | `Icons.BULKY`           |
| Hausratsammlung                          | Hausratsammlung                          | `Icons.BULKY`           |
