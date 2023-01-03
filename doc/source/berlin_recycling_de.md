# Berlin Recycling

Support for schedules provided by [berlin-recycling.de](https://www.berlin-recycling.de/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: berlin_recycling_de
      args:
        username: USERNAME
        password: PASSWORD
```

### Configuration Variables

**username**  
*(string) (required)*

**password**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: berlin_recycling_de
      args:
        username: My User Name
        password: My Password
```
