# Snaga Maribor

Support for schedules provided by [Snaga Maribor](https://snaga-mb.si/), serving Snaga Maribor, Slovenia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: snaga_mb_si
      args:
        street: STREET (Naziv)
        house_number: "HOUSE NUMBER (HS)"
        
```

### Configuration Variables

**street**  
*(String) (required)*
**house_number**  
*(String | Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: snaga_mb_si
      args:
        street: Ruska ulica
        house_number: "24"
        
```

## How to get the source argument

Find the parameter of your address using [https://snaga-mb.si/koledar-odvoza-odpadkov/](https://snaga-mb.si/koledar-odvoza-odpadkov/) and write them exactly like on the web page.
