# Abfuhrkalender Stadt Fürth

Support for schedules provided by <https://abfallwirtschaft.fuerth.eu/>.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_fuerth_eu
      args:
        id: ID
```

### Configuration Variables

**id**
_(integer) (required)_ : The unique 8-digit identifier of your street section

## Example Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: abfallwirtschaft_fuerth_eu
      args:
        id: 96983001  
```

## Example Sensor
```yaml
  - platform: waste_collection_schedule
    name: waste_restabfall
    details_format: "upcoming"
    value_template: '{{ value.daysTo }}'
    types:
      - Restabfall
```	  

## How to get the source arguments

1. Open <https://abfallwirtschaft.fuerth.eu/>.
2. Fill out the filter fields on the page (street and number).
3. click the button "Abfuhrtermine importieren" and right click on "Kalender-Datei herunterladen" selecting "Copy link address". You should get something like this `https://abfallwirtschaft.fuerth.eu/termine.php?icalexport=96983001`
4. Copy the id number at the end of the link to your configuration file.

## Adding Sensors
```yaml
  - platform: waste_collection_schedule
    name: waste_restabfall
    details_format: "upcoming"
    value_template: '{{ value.daysTo }}'
    types:
      - Restabfall
```	  