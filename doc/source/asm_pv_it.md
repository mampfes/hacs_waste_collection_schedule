# ASM Pavia

Support for schedules provided by [ASM Pavia](https://www.asm.pv.it/raccolta-differenziata/porta-a-porta-pavia/) (porta a porta), Italy. Covers Pavia and surrounding municipalities served by ASM, including Albuzzano, Bereguardo, Cava Manara, Certosa di Pavia, Marcignago and others.

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

Municipality (comune) served by ASM Pavia. Either the display name (e.g. `Pavia`) or its slug (e.g. `pavia`) is accepted; matching is case-insensitive.

**street**
*(string) (required)*

Street name as listed on the ASM porta-a-porta lookup. Matching is case-insensitive. For small municipalities served by a single zone, use `Tutte le vie`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: asm_pv_it
      args:
        municipality: "Pavia"
        street: "Via Piemonte"
```

## How to get the source arguments

Open <https://www.asm.pv.it/raccolta-differenziata/porta-a-porta-pavia/>, pick your municipality and street from the search, and use the same values here. The integration only returns the next ~2 weeks of collections — that's all the ASM API exposes.
