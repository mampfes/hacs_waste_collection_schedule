# Merthyr Tydfil County Borough Council

Support for schedules provided by [Merthyr Tydfil County Borough Council](https://www.merthyr.gov.uk).

Source for Merthyr Tydfil County Borough Council waste collections.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: merthyr_gov_uk
      args:
        postcode: POSTCODE
```

### Configuration Variables

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: merthyr_gov_uk
      args:
        postcode: CF47 0AA
```

## How to get the source arguments

Enter your postcode as on the council's collection day page: https://www.merthyr.gov.uk/resident/bins-and-recycling/check-your-collection-day/ If the page reports no results, the postcode is not currently supported by the council's finder.
