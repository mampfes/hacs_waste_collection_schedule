# Gmina Jaktorów

Support for schedules provided by [Gmina Jaktorów](https://bip.jaktorow.pl/odpady-komunalne/harmonogram).

Source for Gmina Jaktorów waste collection schedule (Poland)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: jaktorow_pl
      args:
        region: REGION
```

### Configuration Variables

**region**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: jaktorow_pl
      args:
        region: Rejon 2
```

## How to get the source arguments

Select your collection region (rejon). Most villages are split across regions by street: the schedule PDF linked on https://bip.jaktorow.pl/odpady-komunalne/harmonogram lists the villages and streets of each region at the top of its page (for example, all of Henryszew is in Rejon 6).
