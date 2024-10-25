# Luleå

Support for schedules provided by [Luleå](https://www.lumire.se/), serving Luleå, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: lumire_se
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
    - name: lumire_se
      args:
        address: Storgatan 2
        
```

## How to get the source argument

You can test your address parameter at [https://www.lumire.se/#anch-sokmodul](https://www.lumire.se/#anch-sokmodul).
