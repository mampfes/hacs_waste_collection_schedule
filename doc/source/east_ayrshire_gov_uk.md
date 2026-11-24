# East Ayrshire Council

Support for schedules provided by [East Ayrshire Council](https://www.east-ayrshire.gov.uk/Housing/RubbishAndRecycling/Collection-days/bin-collection-days.aspx).

The council retired its old UPRN calendar. Its [bin collection days](https://www.east-ayrshire.gov.uk/Housing/RubbishAndRecycling/Collection-days/bin-collection-days.aspx) page now uses Routeware's ReCollect platform, which is searched by address and cannot be queried by UPRN, so the source now takes `address` instead of `uprn`.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: east_ayrshire_gov_uk
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Your address as you would type it into the search on the council's [bin collection days](https://www.east-ayrshire.gov.uk/Housing/RubbishAndRecycling/Collection-days/bin-collection-days.aspx) page, for example `1 Main Street` or a property name. The full label shown by the search (e.g. `Church Hall Loudoun Street, Mauchline, KA5 5BZ`) works as well. Upper or lower case does not matter. If more than one property matches, the error message lists their full labels to choose from. A postcode usually covers several properties, so add your house number or property name.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: east_ayrshire_gov_uk
      args:
        address: "Church Hall Lainshaw Street"
```

## Waste types

The food caddy goes out with every bin, so every bin day except garden waste also returns a `Food Waste` collection. With the new collection service the waste types are `General Waste`, `Paper/Card`, `Plastic/Cans`, `Glass`, `Garden Waste` and `Food Waste`. Properties that still have the trolley block get `General Waste`, `Recycling Trolley` and `Food Waste`. The week in which a property moves to the new service shows up as `Transition Week`.

## Moving from `uprn`

Configurations that only contain `uprn` stop working, because the new calendar cannot be searched by UPRN. Replace `uprn` with `address` as shown above. The old waste types `General waste bin`, `Garden waste bin` and `Recycling trolley` are now `General Waste`, `Garden Waste` and `Recycling Trolley`, so `customize` entries for them need renaming.
