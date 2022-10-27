# Abfallsammlung Münchenstein, BL, Switzerland

Support for schedules provided by [https://www.muenchenstein.ch/abfallsammlung](https://www.muenchenstein.ch/abfallsammlung).

This source is just a slight modification of [@atrox06](https://github.com/atrox06)'s work for lindau_ch. So kudos to him.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muenchenstein_ch
      args:
        waste_district: DISTRICT

```

### Configuration Variables

**waste_district**<br>
*(string) (required)*

Valid options for waste_district:
- Abfuhrkreis Ost
- Abfuhrkreis West

or use one the following IDs: 491 for "Ost", 492 for "West"

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muenchenstein_ch
      args:
        waste_district: Abfuhrkreis West

```
