# Staedteservice Raunheim Rüsselsheim

Support for schedules provided by [staedteservice.de](https://www.staedteservice.de/leistungen/abfallwirtschaft/abfallkalender/index.html) location Raunheim and Rüsselsheim.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: staedteservice_de
      args:
        city: CITY
        street_number: STREET NUMBER
```

### Configuration Variables

**city**  
*(string) (required)* _Should be `Raunheim` or ``Rüsselsheim` and not "Rüsselsheim am Main"_

**street_number**  
*(string) (optional)*  _only for compatibility with old configurations_

**street_name**  
*(string) (required if not street_number is provided)*

**house_number**  
*(string|integer)*  

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: staedteservice_de
      args:
        city: "Raunheim"
        street_name: wilhelm-Busch-Straße
        house_number: 3
```

## How to get the source arguments

1. Visit <https://portal.staedteservice.de/calendar/>.
2. Select your `city`, `street`, `house_number`.

### Using street_number

`street_number` was used on an old version of this source, It may work with this newer version. You can still find your internal `street_number` / streetId using your browsers developer tool and inspect the network traffic.
