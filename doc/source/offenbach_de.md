# Offenbach.de 

Support for schedules provided by [Offenbach.de](https://www.offenbach.de/stadtwerke/stadtservice/Entsorgung/abfallkalender.php).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: offenbach_de
      args:
        f_id_location: LocationID
```

### Configuration Variables

**f_id_location**  
*(integer) (required)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: offenbach_de
      args:
        f_id_location: 7036
```

## How to get the source arguments

## Simple Variant: Use wizard script

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/offenbach_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/offenbach_de.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

### Extract arguments from website

Another way get the source arguments is to us a (desktop) browser, e.g. Google Chrome:

1. Open the digital abfallkalender for Offenbach [https://www.offenbach.de/stadtwerke/stadtservice/Entsorgung/abfallkalender.php](https://www.offenbach.de/stadtwerke/stadtservice/Entsorgung/abfallkalender.php).
2. Enter the street name and the number
3. Right click on the iCalendar link and select "Copy Link Address"
4. Paste somewhere like a notepad to get the full URL. Eg: https://www.insert-it.de/BmsAbfallkalenderOffenbach/Main/Calender?bmsLocationId=7036&year=2023
5. The bmsLocationId argument is the location id that you need to use in the configuration as `f_id_location`.
