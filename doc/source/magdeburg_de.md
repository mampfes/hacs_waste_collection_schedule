# Städtischer Abfallwirtschaftsbetrieb Magdeburg

Support for schedules provided by [Städtischer Abfallwirtschaftsbetrieb Magdeburg](https://www.magdeburg.de).

Source for SAB Magdeburg waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: magdeburg_de
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: magdeburg_de
      args:
        street: "Halberst\xE4dter Chaussee 66"
```

## How to get the source arguments

Enter your street name and house number as shown on the SAB Magdeburg website (e.g. 'Halberstädter Chaussee 66'). Search at https://sab.ssl.metageneric.de/app/sab_i_tp/index.php
