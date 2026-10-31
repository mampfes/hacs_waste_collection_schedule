# City of Edinburgh Council

Support for schedules provided by [City of Edinburgh Council](https://www.edinburgh.gov.uk).

Source for Edinburgh kerbside recycling, glass and non-recyclable waste.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: edinburgh_gov_uk
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: edinburgh_gov_uk
      args:
        street: Princess Mary Road
```

## How to get the source arguments

Search for your street at https://www.edinburgh.gov.uk/bin-collection-days under Recycling and waste. Enter the full record name, including any house-number range and Odd/Even suffix. The source follows the current street record and reads its annual PDF, including holiday changes. Green-bin recycling, the glass box and grey-bin waste are supported; food, garden and communal-bin services are not included. The published January grid has a duplicated day number; the complete weekday grid determines that date. An expired calendar fails explicitly.
