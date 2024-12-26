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
 [csv file](https://srrcwastebinserviceday.blob.core.windows.net/wastebinservicedayexport/WasteBinServiceDay_SRRCWebsiteSearch.csv) used by the website. Addresses contain both single-space and double-space character sequences and these need to be preserved.

## Example

```yaml
waste_collection_schedule:
  sources:
  - name: scenicrim_qld_com_au
    args:
      address: "The Old Avocado Farm 77A Long Road TAMBORINE MOUNTAIN  QLD 4272"
```
