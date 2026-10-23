# Noble Environmental

Support for schedules provided by [Noble Environmental](https://nobleenviro.com/).

Source for Noble Environmental (formerly County Hauling), Pennsylvania, US.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nobleenviro_com
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
    - name: nobleenviro_com
      args:
        municipality: Canonsburg
```

## How to get the source arguments

Enter your municipality exactly as Noble Environmental names its calendar PDF (e.g. 'Canonsburg' or 'Springdale Borough'). If you enter only part of the name (e.g. 'Canons'), the error message suggests the matching municipalities. Holiday shifts are taken from the calendar as printed.
