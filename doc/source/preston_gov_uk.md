# Preston City Council

Support for schedules provided by [Preston City Council](https://www.preston.gov.uk/bins), serving the
city of Preston, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: preston_gov_uk
      args:
        street: NUMBER_AND_STREET
        uprn: UPRN
```

### Configuration Variables

**street**
*(string) (optional)*

**uprn**
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: preston_gov_uk
      args:
        street: town hall, lancaster road
        uprn: 10002220003
```

## Exported Bins

  - Commercial Waste (including Recycling)
  - Domestic Waste
  - Garden Waste
  - Recycling (Paper)
  - Recycling (Glass, Plastics, Cans)
