# Kristianstad Renhållning

Support for schedules provided by [Kristianstad Renhållning](https://renhallningen-kristianstad.se).

Source for Kristianstad Renhållning waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: renhallningen_kristianstad_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: renhallningen_kristianstad_se
      args:
        street_address: "\xD6stra Boulevarden 1"
```
