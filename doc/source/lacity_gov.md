# City of Los Angeles, CA

Support for schedules provided by [City of Los Angeles, CA](https://www.lacitysan.org).

Source script for Los Angeles, California waste collection services

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lacity_gov
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lacity_gov
      args:
        street_address: 11050 Pendleton Street
```

## How to get the source arguments

Enter your complete street address within Los Angeles city limits, without city/state. The official GeoQuery API supplies the collection weekday. Black, blue and green bins share this day; the existing LASAN holiday delays are applied. Since the v3 migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
