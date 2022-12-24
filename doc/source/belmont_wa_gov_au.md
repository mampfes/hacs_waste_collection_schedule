# Belmont City Council

Support for schedules provided by [Belmont City Council Waste and Recycling](https://www.belmont.wa.gov.au/live/at-your-place/bins,-waste-and-recycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: belmont_wa_gov_au
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
    - name: belmont_wa_gov_au
      args:
        address: 196 Abernethy Road Belmont 6104
```

## How to get the source arguments

Visit the [Belmont City Council Waste and Recycling](https://www.belmont.wa.gov.au/live/at-your-place/bins,-waste-and-recycling) page and search for your address. The arguments should exactly match the results of the property.