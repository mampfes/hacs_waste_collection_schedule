# Sjöbo kommun

Support for schedules provided by [Sjöbo kommun](https://www.sjobo.se).

Source for Sjöbo kommun waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sjobo_se
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
    - name: sjobo_se
      args:
        address: Gamla torg 10
        city: "Sj\xF6bo"
```

## How to get the source arguments

Enter your street address and city as they appear in the calendar search on https://www.sjobo.se. Collections in a holiday week are marked 'Helgvecka' in the description.
