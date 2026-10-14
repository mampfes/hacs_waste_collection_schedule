# Pendle Borough Council

Support for schedules provided by [Pendle Borough Council](https://www.pendle.gov.uk/binday).

Source for Pendle Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pendle_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
        collection_zone: COLLECTION_ZONE
        garden_waste_bin: GARDEN_WASTE_BIN
        future_collection_dates: FUTURE_COLLECTION_DATES
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

**collection_zone**  
*(string) (optional)*

**garden_waste_bin**  
*(string) (optional)*

**future_collection_dates**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pendle_gov_uk
      args:
        postcode: BB9 7LJ
        address: PENDLE LEISURE TRUST, 1, MARKET STREET, NELSON
```

## How to get the source arguments

Enter the postcode and address as returned by Pendle Borough Council. Set garden_waste_bin to true when the property has a green garden waste bin, and set collection_zone only if Pendle returns multiple schedules for the address.
