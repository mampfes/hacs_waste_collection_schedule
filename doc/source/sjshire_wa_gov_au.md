# Shire of Serpentine Jarrahdale

Support for schedules provided by [Shire of Serpentine Jarrahdale Bins and Collection Dates](https://www.sjshire.wa.gov.au/community/services/waste-and-recycling/bins-and-collection-dates.aspx). Note - this does not account for public holidays (where your rubbish will usually be collected the following day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sjshire_wa_gov_au
      args:
        address: ADDRESS
        predict: PREDICT
```

### Configuration Variables

**address**
*(string) (required)*

**predict**
*(bool) (optional, default=False)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sjshire_wa_gov_au
      args:
        address: 6 Paterson Street MUNDIJONG WA 6123
```

## How to get the source arguments

Visit the [Shire of Serpentine Jarrahdale Bins and Collection Dates](https://www.sjshire.wa.gov.au/community/services/waste-and-recycling/bins-and-collection-dates.aspx) page and search for your address. The `ADDRESS` argument should exactly match the results of the property as shown in the search result.

Currently exporting out:

- Rubbish
- Recycling

## Prediction of future collections

Extrapolation of future collections can be returned using the `PREDICT` boolean as `True`. If enabled, 4 weeks worth of collections will be returned based on the known schedule. Only the first value of each is returned from the search, the rest are predicted.
