# Repentigny (QC)

Support for schedules provided by [Repentigny (QC)](https://collectes-repentigny.coudmain.ca/).

Source script for Ville de Repentigny waste collection using the city's calendar JSON

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: repentigny_ca
      args:
        sector: SECTOR
```

### Configuration Variables

**sector**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: repentigny_ca
      args:
        sector: A
```

## How to get the source arguments

Pick your sector from the <a href="https://repentigny.ca/services/citoyens/collectes">collection calendar</a>.
