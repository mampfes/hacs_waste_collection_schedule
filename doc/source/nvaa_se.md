# NVAA (Norrtälje Vatten och Avfall)

Support for schedules provided by [NVAA](https://www.nvaa.se), Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nvaa_se
      args:
        street_address: STREET ADDRESS
        
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: nvaa_se
      args:
        streetAddress: "Gustav Adolfs väg 24"
```