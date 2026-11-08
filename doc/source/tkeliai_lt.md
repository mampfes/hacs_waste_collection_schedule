# Telšių keliai

Support for schedules provided by [Telšių keliai](https://tkeliai.lt/).

Source script for UAB 'Telšių keliai'

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tkeliai_lt
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
    - name: tkeliai_lt
      args:
        location: Butkų Juzės(1-31) g.
```

## How to get the source arguments

Enter your street or village as the schedules on https://tkeliai.lt/atlieku-tvarkymas list it, e.g. 'Žalioji', 'Butkų Juzės (nuo 1 iki 31)' or 'Paragai'. A street listed in several parts needs its house-number range; a village name that occurs in two elderships needs the eldership, e.g. 'Gintalai, Varnių seniūnija'. The old forms ('Žalioji g.', 'Butkų Juzės(1-31) g.', 'Paragai k.') keep working.
