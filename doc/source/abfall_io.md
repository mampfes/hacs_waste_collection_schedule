# Abfall.IO / AbfallPlus.de

Support for schedules provided by [Abfall.IO](https://abfall.io). The official homepage is using the URL [AbfallPlus.de](https://www.abfallplus.de/) instead.

## Configuration via configuration.yaml

There are to possible ways to configure the Abfall.IO source. The wizzard will automatically return you the correct configuration.

### First way

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

#### Configuration Variables

**key**  
*(hash) (required)*

**f_id_kommune**  
*(integer) (required)*

**f_id_bezirk**  
*(integer) (optional)*

**f_id_strasse**  
*(integer) (required)*

**f_id_strasse_hnr**  
*(string) (optional)*

**f_abfallarten**  
*(list of integer) (optional)*

#### Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io
      args:
        key: "8215c62763967916979e0e8566b6172e"
        f_id_kommune: 2999
        f_id_strasse: 1087
```

### Second way

Currently this configuration is needed by "AWB Landkreis Göppingen".
Other communes might also use this. There is also "AWB Landkreis Böblingen" which can
use both configurations.

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_io
      args:
        key: KEY
        idhousenumber: HOUSENUMBERID
        wastetypes: 
            - 20
            - 17 
            - 59 
            - 18 
            - 19
```

#### Configuration Variables

**key**  
*(hash) (required)*

**idhousenumber**  
*(integer) (required)*

**idhousenumber**  
*(list of integer) (required)*

## How to get the source arguments

## Simple Variant: Use wizard script

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_io.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_io.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

### Hardcore Variant: Extract arguments from website

If you need the first or the second configuration can be seen by the URL. If the URL has the queryparameter `idhousenumber` you need the second configuration.

#### For first configruration way
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


#### For second configruration way

1. Open your county's `Abfuhrtermine` homepage, e.g. [AWB Landkreis Göppingen](https://awb-gp.de/abfallabholung/abfuhrtermine).
2. Enter your data, but don't click on `Datei exportieren` so far!
3. Select `Exportieren als`: `ICS`
4. Open the Developer Tools (Ctrl + Shift + I) and open the `Network` tab.
5. Now click the `Datei exportieren` button.
6. You should see one entry in the network recording.
7. Switch to Payload
8. Copy the paramters `key`, `idhousenumber` and `wastetypes` for your configuration.
