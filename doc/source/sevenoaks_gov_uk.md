# Sevenoaks District Council

Support for schedules provided by [Sevenoaks District Council](https://www.sevenoaks.gov.uk), serving Sevenoaks, Kent, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sevenoaks_gov_uk
      args:
        property_id: PROPERTY_ID
```

### Configuration Variables

**property_id**
*(integer | string) (required)*

The internal numeric property identifier used by Sevenoaks District Council's waste collection day lookup. See below for how to find yours.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sevenoaks_gov_uk
      args:
        property_id: 51621
```

## How to get the source argument

1. Visit <https://sevenoaks-dc-host01.oncreate.app/w/webpage/waste-collection-day>
2. Enter your postcode (with the space) and select your address from the dropdown.
3. Once your collection day loads, note the numeric **property id** — it is the `id=` value at the end of the resulting page URL (e.g. `...&id=51621`).
