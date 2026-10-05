# City of Canning (WA)

Support for schedules provided by [City of Canning (WA)](https://www.canning.wa.gov.au).

Source for City of Canning, Western Australia

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: canning_wa_gov_au
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
    - name: canning_wa_gov_au
      args:
        address: 1325 Albany Highway CANNINGTON  6107
```

## How to get the source arguments

Your address, as it is displayed on the website when showing your collection schedule. Note: There are usually two whitespace characters between the suburb and postal code.
