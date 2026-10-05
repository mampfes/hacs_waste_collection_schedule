# Müllabfuhr Deutschland

Support for schedules provided by [Müllabfuhr Deutschland](https://portal.muellabfuhr-deutschland.de/).

Source for Müllabfuhr, Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muellabfuhr_de
      args:
        client: CLIENT
        city: CITY
        district: DISTRICT
        street: STREET
```

### Configuration Variables

**client**  
*(string) (required)*

**city**  
*(string) (required)*

**district**  
*(string) (optional)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muellabfuhr_de
      args:
        client: Landkreis hildburghausen
        city: Gompertshausen
```

## How to get the source arguments

Enter the district or city (`client`) and the place, district and street as they appear in the waste calendar on https://portal.muellabfuhr-deutschland.de/. District and street are only needed if the place is subdivided further.
