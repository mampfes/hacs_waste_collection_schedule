# Landkreis Rhön Grabfeld

Support for schedules provided by [AbfallInfo Rhön Grabfeld](https://www.abfallinfo-rhoen-grabfeld.de/service/abfuhr-wecker), serving the rural district of Rhön Grabfeld.

API in the background is provided by Offizium.

Possibles types are:
- Restmüll
- Bio
- Gelbe Tonne
- Papier
- Problemmüll

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_rhoen_grabfeld
      args:
        district: DISTRICT
        city: CITY
```

### Configuration Variables

**district** and **city** can be used independently, they can also be omitted to get the calendar for the whole rural district.

**district**
*(string)*

**street**
*(string)*

## Example


```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_rhoen_grabfeld
      args:
        district: "Oberwaldbehrungen"
```

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_rhoen_grabfeld
      args:
        city: "Ostheim"
```

## How to get the source argument

The city and district names used by the API are the same as in the "Stadt, Markt, Gemeinde" and "Ort, Ortsteil" dropdowns on the [collection alarm website](https://www.abfallinfo-rhoen-grabfeld.de/service/abfuhr-wecker).
