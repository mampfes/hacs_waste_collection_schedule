# CM City Media - Müllkalender

Support for schedules provided by [CM City Media - Müllkalender](https://sslslim.cmcitymedia.de/v1/). The official homepage is using the URL [cmcitymedia.de](https://www.cmcitymedia.de/de/startseite) instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cmcitymedia_de
      args:
        hpid: 1
        realmid: 1
        district: 1
```

### Configuration Variables

**hpid**  
*(integer) (required)*

**realmid**  
*(integer) (optional) (automatic grab default one)*

**district**  
*(integer) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cmcitymedia_de
      args:
        hpid: 415
        district: 1371
```

## How to get the source arguments

## Simple Variant: Use wizard script

You can find common hpid values in [https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/service/CMCityMedia.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/service/CMCityMedia.py)

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/citymedia_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/citymedia_de.py)

Run this script from a shell and answer the questions. You start the wizard with option 0.

### Hardcore Variant: Extract arguments from App

1. Decompile the App, extract the source code and search in the source code for hpid or get the hpid from somewhere else
2. Use the Wizard to get the other arguments or use something like postman to get the other arguments from the [API](https://sslslim.cmcitymedia.de/v1/)
