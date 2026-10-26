# Port Adelaide Enfield, South Australia

Support for schedules provided by [Port Adelaide Enfield, South Australia](https://ecouncil.portenf.sa.gov.au/).

Source for City of Port Adelaide Enfield, South Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: portenf_sa_gov_au
      args:
        suburb: SUBURB
        street: STREET
        house_number: HOUSE_NUMBER
        unit_number: UNIT_NUMBER
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**unit_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: portenf_sa_gov_au
      args:
        suburb: Broadview
        street: Regency Road
        house_number: 565
        unit_number: ''
```

## How to get the source arguments

Enter the suburb, street, house number and optional unit number as accepted by https://ecouncil.portenf.sa.gov.au/public/propertywastedates/public.aspx. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
