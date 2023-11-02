# ASR Stadt Chemnitz

Support for schedules provided by [ASR Stadt Chemnitz](https://www.asr-chemnitz.de), serving Chemnitz, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: asr_chemnitz_de
      args:
        street: STRAßE
        house_number: "HAUSNUMMER"
        object_number: "OBJEKT NUMMER"
        
```

### Configuration Variables

**street**  
*(String) (required)*

**house_number**  
*(String | Integer) (required)*

**object_number**  
*(String | Integer) (optional)*

only needed if the selecter asks after entering the house number for an object number

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: asr_chemnitz_de
      args:
        street: Hübschmannstr.
        house_number: "4"
        
```

## How to get the source argument

Find the parameter of your address using https://www.asr-chemnitz.de/kundenportal/entsorgungskalender and write them exactly like on the web page.
