# Rova

Support for schedules provided by [Rova](https://www.rova.nl), a waste collection service operating in several municipalities in the Netherlands (including Raalte, Hardenberg, Ommen, Dalfsen, Zwartewaterland, and others).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rova_nl
      args:
        postalcode: POSTAL CODE
        house_number: HOUSE NUMBER
        addition: ADDITION (optional)
```

### Configuration Variables

**postalcode**
*(String) (required)*

Dutch postal code (4 digits followed by 2 letters, e.g. `8148PC`). Spaces are ignored.

**house_number**
*(String | Integer) (required)*

House number.

**addition**
*(String) (optional, default: `""`)*

House letter or addition. Only required when multiple addresses share the same postal code and house number (e.g. `A`, `bis`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rova_nl
      args:
        postalcode: 8148PC
        house_number: "44"
```

## How to get the source arguments

Use the postal code and house number you would enter on the [Rova afvalkalender](https://www.rova.nl/afvalkalender). If your address has a letter or addition, provide it in the `addition` field.
