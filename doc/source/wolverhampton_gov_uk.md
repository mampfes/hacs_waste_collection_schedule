# Wolverhampton City Council

Support for schedules provided by [Wolverhampton City Council](https://www.wolverhampton.gov.uk).

Source for Wolverhampton City Council waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wolverhampton_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wolverhampton_gov_uk
      args:
        postcode: WV1 1RD
        uprn: '10094887108'
```

## How to get the source arguments

Enter the postcode and UPRN from the council's In Your Area property page. The source follows its View the calendar link and reads the dated calendar supplied by the council, including seasonal gaps. Only services listed for that property are returned. Types now use canonical, localised names; update filters and customisations using old labels.
