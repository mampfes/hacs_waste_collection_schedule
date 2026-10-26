# City of Canterbury-Bankstown (NSW)

Support for schedules provided by [City of Canterbury-Bankstown (NSW)](https://bindayfinder.azurewebsites.net).

City of Canterbury-Bankstown bin day finder

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cbcity_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cbcity_nsw_gov_au
      args:
        address: 102 Crinan Street, Hurlstone Park 2193
```

## How to get the source arguments

Enter your full Canterbury-Bankstown property address, e.g. '102 Crinan Street, Hurlstone Park 2193'. Address punctuation, NSW and common abbreviated street types are accepted. The current published web application supplies the cycle anchor and address-specific bin model. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
