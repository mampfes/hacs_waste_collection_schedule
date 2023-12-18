# Müllabfuhr-Deutschland

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

**district**  
*(string) (optional) not supported by all clients*

**street**  
*(string) (optional) not supported by all clients*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muellabfuhr_de
      args:
        client: "Landkreis Hildburghausen"
        city: "Gompertshausen"
```

```yaml
waste_collection_schedule:
  sources:
    - name: muellabfuhr_de
      args:
        client: Saalekreis
        city: kabelsketal
        district: Großkugel
        street: Am markt
```

```yaml
waste_collection_schedule:
  sources:
    - name: muellabfuhr_de
      args:
        client: saalekreis
        city: Kabelsketal
        district: kleinkugel
```

## How to get the source arguments

goto [muellabfuhr-deutschland](https://portal.muellabfuhr-deutschland.de/)
first copy the name of the client.
second copy the name of the `city`/area (, `district` and `street` if provided)
