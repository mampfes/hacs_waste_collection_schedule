# ZAW (Zentraldeponie Wicker)

Support for schedules provided by [ZAW](https://www.zaw-online.de/), serving multiple cities in Hesse, Germany.

## Configuration via configuration.yaml

`yaml
waste_collection_schedule:
  sources:
    - name: zaw_de
      args:
        city: CITY
        street: STREET
        method: METHOD  # Optional: "api" (default) or "ics"
`

### Configuration Variables

**city**
*(string) (required)*

**street**
*(string) (optional)*

**method**
*(string) (optional, default: "api")*

Choose between "api" for direct API access or "ics" for ICS/iCal format processing. Both methods return the same data.

## Examples

### Using API method (default)

`yaml
waste_collection_schedule:
  sources:
    - name: zaw_de
      args:
        city: "Groß-Zimmern"
        street: "Markstr."
        method: "api"
`

### Using ICS method

`yaml
waste_collection_schedule:
  sources:
    - name: zaw_de
      args:
        city: "Groß-Zimmern"
        street: "Markstr."
        method: "ics"
`

### Without specifying method (uses API by default)

`yaml
waste_collection_schedule:
  sources:
    - name: zaw_de
      args:
        city: "Groß-Zimmern"
        street: "Markstr."
`

## How to get the source arguments

Visit the [ZAW Abfallkalender](https://www.zaw-online.de/abfallkalender/) website and select your city and street. Use these exact values in your configuration.

### Available Cities

The source supports all cities listed on the ZAW website, including but not limited to:
- Groß-Zimmern
- Dieburg
- Münster
- Rödermark
- And many more...
