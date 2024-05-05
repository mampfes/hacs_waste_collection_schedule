# Localcities Bueren, Switzerland

Support for schedules provided by [https://www.localcities.ch/de/entsorgung/bueren-an-der-aare/849](https://www.localcities.ch/de/entsorgung/bueren-an-der-aare/849)


## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: localcities_bueren
      args:
        waste_type:
```

### Configuration Variables

**waste_type**  
*(string) (required)*
(Karton | Altpapier | Grünabfälle)

## Examples

Municipality without extra districts:

```yaml
waste_collection_schedule:
    sources:
    - name: localcities_bueren
      args:
        waste_type: Karton
```

