# Lismore City Council

Support for schedules provided by [Lismore City Council](https://www.lismore.nsw.gov.au/Households/Waste-and-recycling/Whats-My-Bin-Day1).

Source for Lismore City Council waste collection services in NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lismore_city_nsw_gov_au
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
    - name: lismore_city_nsw_gov_au
      args:
        address: 1 Rosella Chase, Goonellabah NSW 2480
```

## How to get the source arguments

Enter the full service address used by Lismore City Council, for example '1 Rosella Chase, Goonellabah NSW 2480'.
