# GOJER

Support for schedules provided by [GOJER](https://www.gojer.at/), serving multiple municipalities in Kernten, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: gojer_at
      args:
        municipality: MUNICIPALITY (Gemeinde)
        city: CITY (ORT)
        
```

### Configuration Variables

**municipality**  
*(String) (required)*

**city**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: gojer_at
      args:
        municipality: Ruden
        city: Kleindiex
```

## How to get the source argument

Find the parameter of your address using [https://www.gojer.at/service/abfuhrkalender.html](https://www.gojer.at/service/abfuhrkalender.html) and write them exactly like on the web page.
