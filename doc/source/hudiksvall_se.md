# Hudiksvall

Support for schedules provided by [Hudiksvall](https://www.hudiksvall.se/), serving Hudiksvall, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hudiksvall_se
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
    - name: hudiksvall_se
      args:
        address: Storgatan 2
        
```

## How to get the source argument

You can test your address parameter at [https://kartor.hudiksvall.se/avfall/hamtning/index_ac.html](https://kartor.hudiksvall.se/avfall/hamtning/index_ac.html).
