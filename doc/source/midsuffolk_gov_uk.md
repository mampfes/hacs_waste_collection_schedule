# Mid Suffolk District Council

Support for bin collection schedules from [Mid Suffolk District Council](https://www.midsuffolk.gov.uk).

> **Note:** From June 2026, Mid Suffolk moved to a three-weekly collection cycle for refuse, recycling, and paper & card, with a separate weekly food-waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: midsuffolk_gov_uk
      args:
        postcode: "IP14 2SA"
        uprn: "10012168792"
```

### Configuration Variables

| Variable | Type | Required | Description |
|----------|------|----------|-------------|
| `postcode` | string | **yes** | Your full postcode, e.g. `IP14 2SA` |
| `uprn` | string | **yes** | Your property's Unique Property Reference Number |

## Finding your UPRN

Visit [https://uprn.uk](https://uprn.uk) or [https://www.findmyaddress.co.uk](https://www.findmyaddress.co.uk) and search for your address. The UPRN is a unique number that identifies your property — for example `10012168792`.

## Examples

### Standard house

```yaml
waste_collection_schedule:
  sources:
    - name: midsuffolk_gov_uk
      args:
        postcode: "IP14 2SA"
        uprn: "10012168792"
```

## Collection types returned

| Type | Icon |
|------|------|
| Refuse Collection (General Rubbish) | `mdi:trash-can` |
| Recycling Collection | `mdi:recycle` |
| Paper & Card Collection | `mdi:newspaper` |
| Food Waste Collection | `mdi:food-apple` |
| Garden Waste Collection (Brown Bin) | `mdi:leaf` |

## Notes

- Garden waste is an optional chargeable subscription — if you are not subscribed it will not appear.
- Bank holiday collection changes are reflected automatically once the council updates their website.
