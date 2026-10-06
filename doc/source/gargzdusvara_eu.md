# Gargždų švara

Support for schedules provided by [Gargždų švara](https://www.gargzdusvara.eu).

Source for VšĮ 'Gargždų švara' waste collection schedules (Klaipėda district municipality, Lithuania).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gargzdusvara_eu
      args:
        location: LOCATION
```

### Configuration Variables

**location**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gargzdusvara_eu
      args:
        location: "Klemi\u0161k\u0117s I k."
```

## How to get the source arguments

Enter the exact location/street-group name as shown in the 'Pasirinkite vietovę' (select location) dropdown on https://www.gargzdusvara.eu/atlieku-isvezimo-grafikai/ after picking any waste type first (e.g. 'Klemiškės I k.'). It must match exactly, including Lithuanian diacritics.
