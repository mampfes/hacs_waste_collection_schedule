# Simbio

Support for schedules provided by [Simbio](https://www.simbio.si/sl/), serving Simbio, Slovenia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: simbio_si
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
    - name: simbio_si
      args:
        street: Ljubljanska cesta
        house_number: "1 A"
        
```

## How to get the source argument

Find the parameter of your address using [https://www.simbio.si/sl/moj-dan-odvoza-odpadkov](https://www.simbio.si/sl/moj-dan-odvoza-odpadkov) and write them exactly like on the web page. 
Some street numbers with character in Simbio database are separate with space so be careful.
