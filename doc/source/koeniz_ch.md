# Köniz

Support for schedules provided by [Köniz](https://koeniz.citymobile.ch).

Source for Köniz

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: koeniz_ch
      args:
        municipality: MUNICIPALITY
        district: DISTRICT
```

### Configuration Variables

**municipality**  
*(string) (required)*

**district**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: koeniz_ch
      args:
        municipality: Wabern
```
