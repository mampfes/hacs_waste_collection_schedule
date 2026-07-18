# Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße

Support for schedules provided by [Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße](https://www.eigenbetrieb-abfallwirtschaft.de).

Source for Eigenbetrieb Abfallwirtschaft Landkreis Spree-Neiße.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eigenbetrieb_abfallwirtschaft_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eigenbetrieb_abfallwirtschaft_de
      args:
        city: '4'
        street: '344'
```
