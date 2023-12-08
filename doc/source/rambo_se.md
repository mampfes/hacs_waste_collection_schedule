# North / Middle Bohuslän - Rambo AB

Support for schedules provided by [North / Middle Bohuslän - Rambo AB](https://www.rambo.se/), serving North / Middle Bohuslän, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rambo_se
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rambo_se
      args:
        address: Grebbestad Ö.långgat./Storg., Grebbestad
        
```

## How to get the source argument

Find the parameter of your address using [https://www.rambo.se/](https://www.rambo.se/) and write them exactly like on the web page.
