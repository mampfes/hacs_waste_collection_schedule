# Trollhättan Energi

Support for schedules provided by [Trollhättan Energi](https://www.trollhattanenergi.se/).

Source for Trollhättan Energi, Trollhättan, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: trollhattanenergi_se
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
    - name: trollhattanenergi_se
      args:
        address: "Albertsv\xE4gen 11"
```

## How to get the source arguments

Enter your street and house number exactly as the address search in Trollhättan Energi's Återvinningsappen shows it, including å, ä and ö (for example 'Albertsvägen 11'). Collections are projected about a year ahead from the next date and interval the app lists for each bin; garden waste only within this year's season.
