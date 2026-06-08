# Rochford District Council

Support for waste collection schedules provided by [Rochford District Council](https://www.rochford.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rochford_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**
*(string) (required)*

The postcode of the property (e.g. `SS4 1AS`).

**uprn**
*(string) (required)*

The composite ward code and UPRN of the property, separated by a hyphen
(e.g. `E05010853-10014203194`). Note this is **not** the bare UPRN — the
ward prefix is required.

## How to find your `uprn`

1. Go to [https://www.rochford.gov.uk/bins-and-collections](https://www.rochford.gov.uk/bins-and-collections).
2. Enter your postcode and press **Find**.
3. An address dropdown appears. Select your address.
4. Open your browser's page source / developer tools and inspect the
   `<select name="uprn">` element. The `value` attribute of your selected
   `<option>` is the composite ward-UPRN you need, e.g.
   `E05010853-10014203194`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rochford_gov_uk
      args:
        postcode: "SS4 1AS"
        uprn: "E05010853-10014203194"
```

## Bin types returned

| Provider description | Returned type     | Icon                  |
|----------------------|-------------------|-----------------------|
| Compost              | `Compost`         | `Icons.GARDEN`        |
| Recyclables          | `Recyclables`     | `Icons.RECYCLING`     |
| Non-recyclables      | `Non-recyclables` | `Icons.GENERAL_WASTE` |
