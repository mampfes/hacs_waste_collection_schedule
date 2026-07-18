# City of Albany

Support for schedules provided by [City of Albany](https://www.albany.wa.gov.au).

Source for City of Albany, Western Australia waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: albany_wa_gov_au
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
    - name: albany_wa_gov_au
      args:
        address: Laithwood Circuit, Marbelup, Albany WA 6330
```

## How to get the source arguments

Enter your street address within the City of Albany (e.g. '15 Melville Street, Albany WA 6330').
