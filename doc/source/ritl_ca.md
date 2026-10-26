# RITL

Support for schedules provided by [RITL](https://ritl.ca/).

Collection calendars published by Régie intermunicipale des Trois-Lacs.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ritl_ca
      args:
        municipality: MUNICIPALITY
        sector: SECTOR
```

### Configuration Variables

**municipality**  
*(string) (required)*

**sector**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ritl_ca
      args:
        municipality: Ivry-sur-le-Lac
        sector: null
```

## How to get the source arguments

Choose a municipality and sector listed under Calendriers de collecte at https://ritl.ca/. The former ICS export has been replaced by the published annual PDFs. Montcalm, Val-David and Val-Morin have no calendar in the current RITL listing. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
