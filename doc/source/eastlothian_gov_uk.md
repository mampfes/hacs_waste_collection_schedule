# East Lothian

Support for schedules provided by [East Lothian Council](https://www.eastlothian.gov.uk/), serving East Lothian, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastlothian_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**postcode**
*(String) (required)*

Your postcode, e.g. `EH21 8GU`.

**address**
*(String) (required)*

Your address, as shown in the dropdown on the council website, e.g. `4 Laing Loan, Wallyford` or `1 Colliers Row, Wallyford`. Commas are optional and will be ignored.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: eastlothian_gov_uk
      args:
        postcode: "EH21 8GU"
        address: "4 Laing Loan, Wallyford"
```

```yaml
waste_collection_schedule:
    sources:
    - name: eastlothian_gov_uk
      args:
        postcode: "EH21 8GX"
        address: "1 Colliers Row, Wallyford"
```

## How to get the source arguments

Go to [https://collectiondates.eastlothian.gov.uk/waste-collection-schedule](https://collectiondates.eastlothian.gov.uk/waste-collection-schedule) and enter your postcode. Select your address from the dropdown. Use the **exact address text** shown in the dropdown (commas and extra spaces are fine, they'll be normalised).
