# Cassowary Coast Regional Council

Support for schedules provided by [Cassowary Coast Regional Council](https://www.cassowarycoast.qld.gov.au).

Source for Cassowary Coast Regional Council, Far North Queensland, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cassowarycoast_qld_gov_au
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
    - name: cassowarycoast_qld_gov_au
      args:
        address: 10 Bombala Street, Mourilyan, 4858
```

## How to get the source arguments

Enter the full service address used by Cassowary Coast Regional Council, for example '10 Bombala Street, Mourilyan, 4858'.
