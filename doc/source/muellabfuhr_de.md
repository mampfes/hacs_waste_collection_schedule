# Müllmax

Support for schedules provided by [muellabfuhr-deutschland](https://portal.muellabfuhr-deutschland.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muellabfuhr_de
      args:
        client: CLIENT_NAME
        city: CITY_NAME
```

### Configuration Variables

**client**  
*(string) (required)*

**city**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muellabfuhr_de
      args:
        client: "Landkreis Hildburghausen"
        city: "Gompertshausen"

```

## How to get the source arguments

goto [muellabfuhr-deutschland](https://portal.muellabfuhr-deutschland.de/)
first copy the name of the client.
second copy the name of the city or area
