# Antrim and Newtownabbey

Support for schedules provided by [Antrim and Newtownabbey](https://antrimandnewtownabbey.gov.uk).

Dated refuse, brown-bin and recycling collections from the council bin checker.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: antrimandnewtownabbey_gov_uk
      args:
        id: ID
        uprn: UPRN
```

### Configuration Variables

**id**  
*(string) (optional)*

**uprn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: antrimandnewtownabbey_gov_uk
      args:
        id: 1456
        uprn: 185354344
```

## How to get the source arguments

Search your address at https://antrimandnewtownabbey.gov.uk/binchecker/ and copy the Id from the selected property's URL into id. The council now publishes dated recycling collections alongside refuse and brown-bin collections. UPRN-only configurations must be updated to this council ID because the old Bryson lookup has been retired; with id configured, the old uprn argument is unnecessary. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
