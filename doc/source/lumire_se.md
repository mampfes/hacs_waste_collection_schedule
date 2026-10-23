# Luleå

Support for schedules provided by [Luleå](https://www.lumire.se/).

Source for Luleå.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lumire_se
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
    - name: lumire_se
      args:
        address: Ringgatan 20
```

## How to get the source arguments

Enter the street address and house number as found by the address search at https://www.lumire.se/ (for example, Ringgatan 20).
