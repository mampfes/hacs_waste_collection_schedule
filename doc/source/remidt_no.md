# ReMidt Orkland muni

Support for schedules provided by [ReMidt Orkland muni](https://www.remidt.no).

Source for Orkland muni.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: remidt_no
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: remidt_no
      args:
        address: Follovegen 1 B
```
