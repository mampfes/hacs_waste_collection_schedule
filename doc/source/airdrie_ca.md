# City of Airdrie (AB)

Support for schedules provided by [City of Airdrie](https://www.airdrie.ca/index.cfm?serviceID=1880), Alberta, Canada.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: airdrie_ca
      args:
        community: COMMUNITY
```

### Configuration Variables

**community**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: airdrie_ca
      args:
        community: "Coopers Crossing"
```

## How to get the source arguments

Visit the [City of Airdrie collection schedules page](https://www.airdrie.ca/index.cfm?serviceID=1880) and select your community from the "Choose your community" dropdown. If you're unsure which community you're in, view the [Waste and recycling community map](https://www.airdrie.ca/getLink.cfm?ID=9274).
