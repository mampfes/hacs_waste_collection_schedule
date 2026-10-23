# Abfallwirtschaft Wiener Neustadt

Support for schedules provided by [Abfallwirtschaft Wiener Neustadt](https://abfall.wiener-neustadt.at/).

Source for abfall.wiener-neustadt.at waste collection schedule for Wiener Neustadt, Austria

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: STREET
        str_id: STR_ID
        rm_art: RM_ART
```

### Configuration Variables

**street**  
*(string) (required)*

**str_id**  
*(string) (optional)*

**rm_art**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: Martinsgasse
        rm_art: monatlich
```

## How to get the source arguments

Visit the website https://abfall.wiener-neustadt.at/ and select your street from the dropdown menu. Note your street name and select the waste collection frequency that applies to your address.
