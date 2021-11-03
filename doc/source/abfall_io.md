# Abfall.IO / AbfallPlus.de

Support for schedules provided by [Abfall.IO](https://abfall.io). The official homepage is using the URL [AbfallPlus.de](https://www.abfallplus.de/) instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io
      args:
        key: KEY
        f_id_kommune: KOMMUNE
        f_id_bezirk: BEZIRK
        f_id_strasse: strasse
        f_id_strasse_hnr: HNR
        f_abfallarten:
          - 1
          - 2
          - 3
```

### Configuration Variables

**key**<br>
*(hash) (required)*

**f_id_kommune**<br>
*(integer) (required)*

**f_id_bezirk**<br>
*(integer) (optional)*

**f_id_strasse**<br>
*(integer) (required)*

**f_id_strasse_hnr**<br>
*(string) (optional)*

**f_abfallarten**<br>
*(list of integer) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io
      args:
        key: "8215c62763967916979e0e8566b6172e"
        f_id_kommune: 2999
        f_id_strasse: 1087
```

## How to get the source arguments

## Simple Variant: Use wizard script

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_io.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_io.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

### Hardcore Variant: Extract arguments from website

Another way get the source arguments is to us a (desktop) browser with developer tools, e.g. Google Chrome:

1. Open your county's `Abfuhrtermine` homepage, e.g. [https://www.lrabb.de/start/Service+_+Verwaltung/Abfuhrtermine.html](https://www.lrabb.de/start/Service+_+Verwaltung/Abfuhrtermine.html).
2. Enter your data, but don't click on `Datei exportieren` so far!
3. Select `Exportieren als`: `ICS`
4. Open the Developer Tools (Ctrl + Shift + I) and open the `Network` tab.
5. Now click the `Datei exportieren` button.
6. You should see one entry in the network recording.
7. Select the entry on the left hand side and scroll down to `Query String Parameters` on the right hand side.
8. Here you can find the value for `key`.
9. Now go down to the next section `Form Data`.
10. Here you can find the values for `f_id_kommune`, `f_id_bezirk`, `f_id_strasse`, `f_id_strasse_hnr` and `f_abfallarten`. All other entries don't care.
