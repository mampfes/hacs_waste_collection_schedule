# Landkreis Rhön Grabfeld

Support for schedules provided by [AbfallInfo Rhön Grabfeld](https://www.abfallinfo-rhoen-grabfeld.de/service/abfuhr-wecker), serving the rural district of Rhön Grabfeld.

Api in the background is provided by Offizium.

Possibles types are:
- Restmüll/Gelber Sack/Biotonne
- Papiersammlung
- Problemmüllsammlung

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_landkreis_rhoen_grabfeld
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

To get the names used by the api navigate to the [collection alarm website](https://www.abfallinfo-rhoen-grabfeld.de/service/abfuhr-wecker), enter your city and district, select "Aktuelles Jahr als .ics-Datei exportieren" and copy the parameters from the corresponding download url.
