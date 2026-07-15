# Gemeinde Hasselroth

Support for schedules provided by [Gemeinde Hasselroth](https://www.hasselroth.de), serving Hasselroth, Hesse, Germany.

Hasselroth publishes one ICS calendar file per district (Ortsteil) and year on its website. This source automatically finds the current download link for the requested district.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hasselroth_de
      args:
        district: DISTRICT
```

### Configuration Variables

**district**
*(String) (required)*

The Hasselroth district (Ortsteil): one of `Neuenhasslau`, `Niedermittlau` or `Gondsroth`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: hasselroth_de
      args:
        district: Neuenhasslau
```

## How to get the source argument

Hasselroth consists of three districts (Ortsteile): `Neuenhasslau`, `Niedermittlau` and `Gondsroth`. Use the name of the district your address belongs to.

You can find the published calendars at [https://www.hasselroth.de/buergerportal/rathaus/abfallentsorgung/ics/](https://www.hasselroth.de/buergerportal/rathaus/abfallentsorgung/ics/).
