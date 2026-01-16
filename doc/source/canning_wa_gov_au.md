# City of Canning (WA)

Support for schedules provided by [City of Canning](https://www.canning.wa.gov.au/residents/waste-and-recycling/), WA.

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
Your address, as it is displayed on the website when showing your collection schedule.

_Note_: There are usually two whitespace characters between the suburb and postal code.


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: canning_wa_gov_au
      args:
        address: "12 Battersea Road CANNING VALE  6155" # note the whitespace
```
