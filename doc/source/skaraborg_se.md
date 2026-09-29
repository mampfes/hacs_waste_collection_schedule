# Avfall & Återvinning Skaraborg

Support for schedules provided by [Avfall & Återvinning Skaraborg](https://avfallskaraborg.se/).

Source for Skaraborg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: skaraborg_se
      args:
        address: ADDRESS
        city: CITY
```

### Configuration Variables

**address**  
*(string) (required)*

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: skaraborg_se
      args:
        address: "Gran\xE4ngsv\xE4gen 1"
        city: "Sk\xF6vde"
```

## How to get the source arguments

Enter your street address and city exactly as they appear when you search for your address on https://avfallskaraborg.se/.
