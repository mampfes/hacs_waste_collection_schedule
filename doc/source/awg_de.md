# ZAW Donau-Wald

Support for schedules provided by [ZAW Donau-Wald](https://www.awg.de/).

Source for ZAW Donau-Wald.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awg_de
      args:
        city: CITY
        street: STREET
        hnr: HNR
        addition: ADDITION
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**hnr**  
*(string) (required)*

**addition**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awg_de
      args:
        city: Achslach
        street: Aign
        hnr: '1'
```
