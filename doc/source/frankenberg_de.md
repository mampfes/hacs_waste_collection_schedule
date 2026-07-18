# Stadt Frankenberg (Eder)

Support for schedules provided by [Stadt Frankenberg (Eder)](https://www.frankenberg.de/).

Source for Stadt Frankenberg (Eder).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: frankenberg_de
      args:
        district: DISTRICT
        street: STREET
```

### Configuration Variables

**district**  
*(string) (required)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: frankenberg_de
      args:
        district: "Vierm\xFCnden"
```
