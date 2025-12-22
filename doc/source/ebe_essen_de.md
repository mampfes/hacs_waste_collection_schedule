# EBE Essen

Support for schedules provided by [EBE Essen (Entsorgungsbetriebe Essen)](https://www.ebe-essen.de/), serving the city of Essen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ebe_essen_de
      args:
        street_id: STREET_ID
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street_id**
*(string) (required)*

The street ID can be found by inspecting the network traffic on the [EBE Abfuhrkalender](https://www.ebe-essen.de/service-info/abfallabfuhr/#kalender) website.

**house_number**
*(string) (required)*

Your house number (e.g., "15", "3a")

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ebe_essen_de
      args:
        street_id: "2175"
        house_number: "15"
```

## How to get the source arguments

1. Visit the [EBE Abfuhrkalender](https://www.ebe-essen.de/service-info/abfallabfuhr/#kalender)
2. Open your browser's Developer Tools (F12)
3. Go to the Network tab
4. Select your street and house number
5. Look for a POST request to `widgets.abfall.io/graphql` with "GetHouseNumbers" in the payload
6. In the request payload, find the `streetId` value
7. Use this value as `street_id` in your configuration

### Waste Types

The source automatically detects the following waste types for your address:
- Blaue Tonne (Paper)
- Braune Tonne (Organic waste)
- Gelbe Tonne (Packaging)
- Graue Tonne (Residual waste)
- Schadstoffmobil (Hazardous waste collection vehicle)
- Weihnachtsbäume (Christmas trees)
