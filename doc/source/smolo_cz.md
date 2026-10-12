# SMOLO a.s. (Třinec)

Support for schedules provided by [SMOLO a.s. (Třinec)](https://www.smolo.cz/sluzby/odpadove-hospodarstvi/informace-pro-domacnosti/).

Source for SMOLO a.s. household waste collection schedule for the town of Třinec, Czech Republic.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: smolo_cz
      args:
        district: DISTRICT
        street: STREET
```

### Configuration Variables

**district**  
*(string) (required)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: smolo_cz
      args:
        district: Nebory
```

## How to get the source arguments

Open the SMOLO a.s. household-waste page (https://www.smolo.cz/sluzby/odpadove-hospodarstvi/informace-pro-domacnosti/) and look up the current 'Třinec - harmonogram' PDF for the SKO/BIO/SEP schedule. Use the 'ČÁST MĚSTA' (part of town) column value as the district, e.g. 'Staré Město', 'Lyžbice', 'Nebory' or 'Karpentná'. If your district appears in several rows with different street lists, also set the street to one street name from the 'LOKALITA' column.
