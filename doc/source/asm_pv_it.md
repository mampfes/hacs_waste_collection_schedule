# ASM Pavia

Support for schedules provided by [ASM Pavia](https://www.asm.pv.it).

Source for ASM Pavia (porta a porta) waste collection in Pavia and surrounding municipalities, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: asm_pv_it
      args:
        municipality: MUNICIPALITY
        street: STREET
```

### Configuration Variables

**municipality**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: asm_pv_it
      args:
        municipality: Pavia
        street: Via Piemonte
```

## How to get the source arguments

Open https://www.asm.pv.it/raccolta-differenziata/porta-a-porta-pavia/ and pick your municipality and street from the search. Use the same values here. For small municipalities served by a single zone, use 'Tutte le vie' as the street.
