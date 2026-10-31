# Waverley Council

Support for schedules provided by [Waverley Council](https://www.waverley.nsw.gov.au).

Source for Waverley Council (NSW) kerbside collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: waverley_nsw_gov_au
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
    - name: waverley_nsw_gov_au
      args:
        address: 585 Old South Head Road, Rose Bay NSW 2029
```

## How to get the source arguments

Enter your address as the council's 'Find your collection day' search lists it, e.g. '1 Aboukir Street Dover Heights' or a unit as '2/585 Old South Head Road Rose Bay' (state and postcode are optional). A whole building's address works when all its units share one waste zone.
