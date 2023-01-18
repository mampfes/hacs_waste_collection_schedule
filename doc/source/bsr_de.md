# Berliner Stadtreinigungsbetriebe

Support for schedules provided by [bsr.de](https://www.bsr.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        abf_strasse: STRASSE
        abf_hausnr: HAUSNR
```

### Configuration Variables

**abf_strasse**  
*(string) (required)*

**abf_hausnr**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        abf_strasse: "Bahnhofstr., 12159 Berlin (Tempelhof-Schöneberg)"
        abf_hausnr: 1
```

## How to get the source arguments

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/bsr_de.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/bsr_de.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.
