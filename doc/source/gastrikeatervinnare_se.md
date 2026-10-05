# Gästrike Återvinnare

Support for schedules provided by [Gästrike Återvinnare](https://gastrikeatervinnare.se/).

Source for Gästrike Återvinnare waste collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gastrikeatervinnare_se
      args:
        street: STREET
        city: CITY
```

### Configuration Variables

**street**  
*(string) (required)*

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gastrikeatervinnare_se
      args:
        street: "Nedre V\xE4gen 52"
        city: "\xC5rsunda"
```

## How to get the source arguments

Enter your street name with house number and your city exactly as shown on https://gastrikeatervinnare.se/ when you search for your collection days.
