# SICTOM du Val de Saône

Support for schedules provided by [SICTOM du Val de Saône](https://www.sictomvds.com).

Source for SICTOM du Val de Saône waste collection schedules in Haute-Saône, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sictomvds_com
      args:
        commune: COMMUNE
```

### Configuration Variables

**commune**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sictomvds_com
      args:
        commune: Velleminfroy
```

## How to get the source arguments

Enter your commune as it is named on the map at https://www.sictomvds.com (for example 'Velleminfroy').
