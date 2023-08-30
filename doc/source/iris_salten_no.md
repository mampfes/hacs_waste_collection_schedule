# IRiS

Support for schedules provided by [IRiS](https://www.iris-salten.no), serving multiple, Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: iris_salten_no
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

**kommune**
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: iris_salten_no
      args:
        address: Alsosgården 11, bodø
        
```

## How to get the source argument

Find the parameter of your address using [https://www.iris-salten.no/tommekalender/](https://www.iris-salten.no/tommekalender/) and write them exactly like on the web page.
