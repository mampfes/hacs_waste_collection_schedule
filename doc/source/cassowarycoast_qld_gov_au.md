# Cassowary Coast Regional Council

Support for schedules provided by [Cassowary Coast Regional Council](https://www.cassowarycoast.qld.gov.au/Waste-Water-and-Roads/Waste-and-Recycling/Kerbside-Collection), Far North Queensland, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cassowarycoast_qld_gov_au
      args:
        address: YOUR_FULL_ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Your full street address including suburb, exactly as it appears in the Cassowary Coast Regional Council bin-day search.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cassowarycoast_qld_gov_au
      args:
        address: "10 Bombala Street, Mourilyan, 4858"
```

## How to get the source arguments

1. Visit the [Cassowary Coast Regional Council Kerbside Collection page](https://www.cassowarycoast.qld.gov.au/Waste-Water-and-Roads/Waste-and-Recycling/Kerbside-Collection).
2. Enter your street address in the "Enter street address to find your collection dates" search tool.
3. Use the full address exactly as shown in the search result.

This source covers the Cassowary Coast Regional Council local government area in Far North Queensland, including localities such as Innisfail, Tully, Cardwell, and Mourilyan. Actual service coverage is determined by the council lookup.
