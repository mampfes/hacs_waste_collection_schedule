# Laval (QC)

Laval (QC) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- If you don't know your sector, go to `https://www.laval.ca/recherche-par-adresse/` and enter your address to identify your house matricule and zone.
- Right-click 'Add to my calendar' and select `Copy link address`.
- Use this copied URL as the `url` parameter.
- You can trim the tracking data after the `codeZone=#`

## Examples

### Default

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: Collecte\s*-\s(\w+)
        url: https://api-prd.laval.ca/ext/sitewebsearch-ext/v1/collecte/export-ics?matricule=8546-45-9730-2-000-0000&codeZone=12
```
