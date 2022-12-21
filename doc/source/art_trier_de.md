# ART Trier

Support for schedules provided by <https://www.art-trier.de>.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: art_trier_de
      args:
        zip_code: ZIP_CODE
        district: DISTRICT
```

### Configuration Variables

**district**<br>
_(string) (required)_

**zip_code**<br>
_(string) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cochem_zell_online_de
      args:
        district: "Wittlich, Marktplatz"
        zip_code: "54516"
```

## How to get the source arguments

1. Open <https://www.art-trier.de/cms/abfuhrtermine-1002.html>.
2. Fill out the search field on the right side of the page.
3. Open one of the matching results (if multiple years are shown, click on either of them, it does not matter).
4. Copy the _complete_ name of the city on the top left (it may contain a street name or suburbs) and paste it to the field `district`
5. Enter your ZIP code (Postleitzahl) in the field `zip_code`. This value is also shown next to the district name on the results overview page.
