# Müllmann-App

Support for schedules provided by [Müllmann-App](https://muellmann-app.de/).

Source for Müllmann-App, providing waste collection schedules for several municipalities around Lake Constance (Bodensee), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muellmann_app_de
      args:
        city: CITY
        street: STREET
        range_selector: RANGE_SELECTOR
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (optional)*

**range_selector**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muellmann_app_de
      args:
        city: Radolfzell
        street: "Mooser Stra\xDFe"
```

## How to get the source arguments

Enter the municipality name (see the source's supported places list). For municipalities with street-level schedules, also provide your street name. If your street is split into several collection areas, add the correct 'range_selector' value; the error message you get on first try will list the valid options for your street.
