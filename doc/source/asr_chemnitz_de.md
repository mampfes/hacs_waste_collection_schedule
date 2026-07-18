# ASR Stadt Chemnitz

Support for schedules provided by [ASR Stadt Chemnitz](https://www.asr-chemnitz.de).

Source for ASR Stadt Chemnitz.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: asr_chemnitz_de
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        object_number: OBJECT_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**object_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: asr_chemnitz_de
      args:
        street: "H\xFCbschmannstr."
        house_number: '4'
```
