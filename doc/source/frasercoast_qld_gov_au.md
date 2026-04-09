# Fraser Coast Regional Council

Support for schedules provided by [Fraser Coast Regional Council](https://www.frasercoast.qld.gov.au/Services/Online-Services/Check-your-bin-day), serving the Hervey Bay, Maryborough, and surrounding areas of Queensland, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: frasercoast_qld_gov_au
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
    - name: frasercoast_qld_gov_au
      args:
        address: "57 Arbornine Road Glenwood"
```

## How to get the source arguments

Visit the [Fraser Coast Check Your Bin Day](https://www.frasercoast.qld.gov.au/Services/Online-Services/Check-your-bin-day) page and search for your address.
