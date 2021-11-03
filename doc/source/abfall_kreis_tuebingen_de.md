# Abfall Kreis Tübingen

Support for schedules provided by [abfall-kreis-tuebingen.de](https://www.abfall-kreis-tuebingen.de).

![](https://www.abfall-kreis-tuebingen.de/wp-content/themes/twentysixteen_child/images/ABW_Logo_600_250.png)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kreis_tuebingen_de
      args:
        ort: ORT
        dropzone: DROPZONE
        ics_with_drop: ICS_WITH_DROP
```

### Configuration Variables

**ort**<br>
*(integer) (required)*

**dropzone**<br>
*(integer) (required)*

**ics_with_drop**<br>
*(boolean) (optional, default: ```False```)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kreis_tuebingen_de
      args:
        ort: 3
        dropzone: 525
```

## How to get the source arguments

### Simple Variant: Use wizard script

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_kreis_tuebingen_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/abfall_kreis_tuebingen_de.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

### Hardcore Variant: Extract arguments from website

Another way get the source arguments is to extract the arguments from the website using a (desktop) browser with developer tools, e.g. Google Chrome:

1. Open [https://www.abfall-kreis-tuebingen.de/services/online-abfuhrtermine/](https://www.abfall-kreis-tuebingen.de/services/online-abfuhrtermine/).
2. Enter your data, but don't click on "ICS Download" so far!
3. Open the Developer Tools (Ctrl + Shift + I) and open the `Network` tab.
4. Now click the "ICS Download" button.
5. You should see (amongst other's) one entry labeled `admin-ajax.php` in the network recording.
6. Select `admin-ajax.php` on the left hand side and scroll down to `Form Data` on the right hand side.
7. Here you can find the values for `ort` and `dropzone`.
