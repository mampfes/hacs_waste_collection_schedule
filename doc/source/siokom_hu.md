# Siókom Nonprofit Kft.

Support for schedules provided by [Siókom Nonprofit Kft.](https://www.siokom.hu).

Source for Siókom Nonprofit Kft. waste calendars (Siófok and surrounding settlements, Hungary).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: siokom_hu
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: siokom_hu
      args:
        area: "Balatonvil\xE1gos"
```

## How to get the source arguments

Open https://www.siokom.hu/jaratterv/ and copy the settlement or district name exactly as listed (e.g. 'Balatonvilágos', 'Siófok Cs-v', 'Zamárdi Kőhegy'). Use the short name, not the neighbourhood description under Siófok rows. There is no street selector.
