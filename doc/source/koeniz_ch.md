# Köniz, Switzerland

Support for schedules provided by [Köniz.ch](https://koeniz.citymobile.ch)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: koeniz_ch
      args:
        municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: koeniz_ch
      args:
        municipality: Wabern
```

## How to get the source argument

Open [Abfallkalender Köniz](https://koeniz.citymobile.ch/index.php?apid=6297623&apparentid=9293364) which shows a list of all municipalities. Select your municipality from the list.