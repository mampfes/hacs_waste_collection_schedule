# City of Monash Council

Support for schedules provided by [City of Monash](https://www.monash.vic.gov.au/Waste-Sustainability/Bin-Collection/When-we-collect-your-bins).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: monash_vic_gov_au
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
    - name: monash_vic_gov_au
      args:
        address: 4 Carson Street, Mulgrave 3170
```

## How to get the source arguments

Visit the City of Monash [When we collect your bins](https://www.monash.vic.gov.au/Waste-Sustainability/Bin-Collection/When-we-collect-your-bins) page and search for your address. For example: ```4 Carson Street, Mulgrave 3170```. The **address** variable should exactly match the full street address after selecting the autocomplete result.'
