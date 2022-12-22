# Abfallwirtschaftsbetriebe Köln

Support for schedules provided by [awbkoeln.de](https://www.awbkoeln.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awbkoeln_de
      args:
        street_code: STREET_CODE
        building_number: BUILDING_NUMBER
```

### Configuration Variables

**street_code**<br>
*(string) (required)*

**building_number**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awbkoeln_de
      args:
        street_code: 4272
        building_number: 10
```

## How to get the source arguments

### Script

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/awbkoeln_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/awbkoeln_de.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

### Manually

It is also possible to retrieve the `street_code` manually. For this, you need to go to the following AWB-page and enter an address:

[https://www.awbkoeln.de/abfuhrkalender/](https://www.awbkoeln.de/abfuhrkalender/)

Afterwards you can hover over the PDF-download, labelled "Jahres-Abfuhrkalender XXXX als PDF", which should show you an URL similar to this one for the Kölner Dom:

[https://www.awbkoeln.de/sensis/pdfcal/genpdf.php?p_strasse=Domkloster&p_hausnr=4&p_strnr=745&u_strasse=Domkloster&u_hausnr=4&j=23](https://www.awbkoeln.de/sensis/pdfcal/genpdf.php?p_strasse=Domkloster&p_hausnr=4&p_strnr=745&u_strasse=Domkloster&u_hausnr=4&j=23)

The number after `p_strnr=`, in this example `745`, is then what you can add as `street_code` in your YAML.
