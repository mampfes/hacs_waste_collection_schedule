# Landkreis Nordwestmecklenburg

Support for Landkreis Nordwestmecklenburg in Mecklenburg-Vorpommern, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: geoport_nwm_de
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

### How to get the source arguments

Visit [geoport-nwm.de](https://www.geoport-nwm.de/de/abfuhrtermine-geoportal.html) and search for your area. Copy the value from the text input field and use it for the `district` argument. It is case sensitive.