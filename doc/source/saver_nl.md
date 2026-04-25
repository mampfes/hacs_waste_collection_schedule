# Saver

Support for schedules provided by [Saver](https://saver.nl/afvalkalender), the waste collector for the West-Brabant region in the Netherlands. Covers Roosendaal, Halderberge, Bergen op Zoom, Rucphen, Zundert, Steenbergen, and Woensdrecht.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: saver_nl
      args:
        postcode: POSTCODE
        huisnummer: HOUSE_NUMBER
        toevoeging: ADDITION  # optional
```

### Configuration Variables

**postcode**
*(string) (required)*

Dutch postal code (4 digits + 2 letters), e.g. `4702AA`. Spaces are accepted and stripped.

**huisnummer**
*(string | integer) (required)*

House number.

**toevoeging**
*(string) (optional)*

House letter or addition (e.g. `a`, `bs`). Only required when more than one address shares the same `postcode` + `huisnummer`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: saver_nl
      args:
        postcode: "4702AA"
        huisnummer: "1"
```

## How to get the source arguments

Use the same postcode and house number you would enter at <https://saver.nl/afvalkalender>. If the calendar lookup shows multiple matching addresses, set `toevoeging` to the letter or addition shown there.
