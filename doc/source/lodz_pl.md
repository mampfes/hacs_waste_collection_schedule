# Łódź

Support for schedules provided by [Miasto Łódź](https://uml.lodz.pl/) via the [Karta Łodzianina](https://kartalodzianina.pl/wywoz-odpadow) portal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lodz_pl
      args:
        street: "Piotrkowska"
        house_number: "104"
        building_type: 2
```

### Configuration Variables

**street** *(string) (required)* Name of the street (e.g., `"Piotrkowska"`, `"Podchorążych"`).

**house_number** *(string) (required)* House number, optionally including a letter (e.g., `"104"`, `"2a"`).

**building_type** *(int) (optional)* Type of the building. Allowed values:
* `1` - Single-family house (jednorodzinna) *(Default)*
* `2` - Multi-family building / Block of flats (wielorodzinna)
* `3` - Summer house (letniskowa)

## Examples

### Single-family house (Default building type)
```yaml
waste_collection_schedule:
  sources:
    - name: lodz_pl
      args:
        street: "Partyzantów"
        house_number: "1"
```

### Multi-family building
```yaml
waste_collection_schedule:
  sources:
    - name: lodz_pl
      args:
        street: "Piotrkowska"
        house_number: "104"
        building_type: 2
```

### Summer house
```yaml
waste_collection_schedule:
  sources:
    - name: lodz_pl
      args:
        street: "Podchorążych"
        house_number: "1"
        building_type: 3
```

## How to get the source arguments

You need to provide your exact street name and house number as registered in the official city database.

You can verify your address and the corresponding building type by accessing the official [Karta Łodzianina Garbage Collection Schedule](https://kartalodzianina.pl/wywoz-odpadow). Simply fill out the search form on their website to ensure your `street`, `house_number`, and `building_type` parameters match the system records.