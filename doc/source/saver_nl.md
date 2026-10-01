# Saver

Support for schedules provided by [Saver](https://saver.nl).

Source for Saver waste collection in West-Brabant (Roosendaal, Halderberge, Bergen op Zoom, Rucphen, Zundert, Steenbergen, Woensdrecht).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: saver_nl
      args:
        postcode: POSTCODE
        huisnummer: HUISNUMMER
        toevoeging: TOEVOEGING
```

### Configuration Variables

**postcode**  
*(string) (required)*

**huisnummer**  
*(string) (required)*

**toevoeging**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: saver_nl
      args:
        postcode: 4702AA
        huisnummer: 1
```

## How to get the source arguments

Use the same postcode and house number you would enter at https://saver.nl/afvalkalender. If your address has a letter or addition (e.g. '5a'), provide the letter/addition in the 'toevoeging' argument.
