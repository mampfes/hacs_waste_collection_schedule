# Taranto (araccolta.it)

Support for schedules provided by [Taranto (araccolta.it)](https://araccolta.it/), serving Taranto, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: araccolta_it
      args:
        district: DISTRICT (Quartiere)
        domestic: DOMESTIC (Utenze Domestiche)
```

### Configuration Variables

**district**  
*(String) (required)*

**domestic**  
*(Integer) (optional, default=True)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: araccolta_it
      args:
        district: lama-san-vito-talsano
        domestic: True
```

## How to get the source argument

Visit [https://araccolta.it/#calendario](https://araccolta.it/#calendario) and select your district (Quartiere) write the argument exactly like in the URL after clicking on your district.
