# Hudiksvall

Support for schedules provided by [Hudiksvall](https://www.hudiksvall.se).

Source for Hudiksvall.

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hudiksvall_se
      args:
        address: Trädgårdsgatan 4 Hudiksvall
```
