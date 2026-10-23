# AWB Ammerland

Support for schedules provided by [AWB Ammerland](https://www.awb-ammerland.de).

Source for AWB Ammerland (Abfallwirtschaftsbetrieb Landkreis Ammerland).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_ammerland_de
      args:
        city: CITY
        street: STREET
        street_section: STREET_SECTION
        four_weekly_rest: FOUR_WEEKLY_REST
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**street_section**  
*(string) (optional)*

**four_weekly_rest**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_ammerland_de
      args:
        city: Edewecht
        street: Schepser Damm
```

## How to get the source arguments

Only required if the street is divided into sections (e.g. 'nördl.d. A 28'). Enable if a 4-weekly collection interval for residual waste has been requested.
