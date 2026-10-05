# Tauranga City Council

Support for schedules provided by [Tauranga City Council](https://www.tauranga.govt.nz/).

Source script for Tauranga City Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tauranga_govt_nz
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
    - name: tauranga_govt_nz
      args:
        address: 121 Castlewold Drive
```

## How to get the source arguments

Enter your street address as you would on the council's [when to put your bins out](https://www.tauranga.govt.nz/services/rubbish-and-recycling/kerbside-collections/when-to-put-your-bins-out) page.
