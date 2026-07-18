# Berliner Stadtreinigungsbetriebe

Support for schedules provided by [Berliner Stadtreinigungsbetriebe](https://bsr.de).

Source for Berliner Stadtreinigungsbetriebe waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        schedule_id: SCHEDULE_ID
```

### Configuration Variables

**schedule_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bsr_de
      args:
        schedule_id: 04901100010300413840045A
```
