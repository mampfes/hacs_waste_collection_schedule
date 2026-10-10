# City of Doncaster Council

Support for schedules provided by [City of Doncaster Council](https://www.doncaster.gov.uk/services/bins-recycling-waste), serving the city of Doncaster, UK.

The council moved its bin lookup to <https://doncaster-wasterecycling.oncreate.app/w/webpage/bin-query> in October 2026. That lookup works from a postcode and a house number or name and does not accept a UPRN, so the source now takes `postcode` and `address` instead of `uprn`.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: doncaster_gov_uk
      args:
        postcode: POSTCODE
        address: HOUSE_NUMBER_OR_NAME
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

The house number or name of the property, as you would type it into the "Property Number or Name" box of the council's bin lookup, for example `12` or `Rose Cottage`. It has to match the start of the address (`1` finds `1 High Street` but not `10 High Street`). Commas and upper or lower case do not matter. If more than one property matches, the error message lists their full addresses to choose from, and you can use one of them as `address`. If nothing matches, the error message lists the addresses on the first result page of the council's lookup (up to 25).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: doncaster_gov_uk
      args:
        postcode: "DN6 0LF"
        address: "Askern Methodist Church"
```

## Moving from `uprn`

Configurations that only contain `uprn` stop working, because the new council lookup cannot be queried by UPRN. Replace `uprn` with `postcode` and `address` as shown above. The waste types are now the names the new page uses: `Refuse`, `Recycling` and `Green Garden Waste Collection Service`. The old source matched `Black`, `Green`, `Recycling`, `Bulky` and the bulky reuse collection in its icon map, so `customize` entries for `Black` and `Green` most likely need renaming.

## How to get the source arguments

Open the council's [bin lookup](https://doncaster-wasterecycling.oncreate.app/w/webpage/bin-query), enter your postcode and, if you like, your house number or name, and use the same values as `postcode` and `address`.
