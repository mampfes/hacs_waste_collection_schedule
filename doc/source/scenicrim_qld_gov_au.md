# Scenic Rim Regional Council

Support for schedules provided by [Scenic Rim Regional Council](https://scenicrim.qld.gov.au), serving Scenic Rim Regional Council in Queensland, Australia

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: scenicrim_qld_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (mandatory)*

Your address as it appears in the _Street_Address_ column of the
 [csv file](https://srrcwastebinserviceday.blob.core.windows.net/wastebinservicedayexport/WasteBinServiceDay_SRRCWebsiteSearch.csv) used by the website. Case and spacing do not have to match: the register's double spaces and upper-casing are ignored when matching, so `77a long road tamborine mountain qld 4272` finds the same property.

If the address is not found, the error message lists the closest matching entries from the register.

A small number of properties are listed in the register with a _Recycle_Week_ of `Contact Council` rather than a red/blue week. For those, only the general waste collection is reported; contact the council for the recycling schedule.

## Example

```yaml
waste_collection_schedule:
  sources:
  - name: scenicrim_qld_com_au
    args:
      address: "The Old Avocado Farm 77A Long Road TAMBORINE MOUNTAIN  QLD 4272"
```
