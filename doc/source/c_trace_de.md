# C-Trace

Support for schedules provided by [C-Trace](https://c-trace.de/).

Source for C-Trace.de.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: c_trace_de
      args:
        strasse: STRASSE
        hausnummer: HAUSNUMMER
        gemeinde: GEMEINDE
        ort: ORT
        ortsteil: ORTSTEIL
        service: SERVICE
        abfall: ABFALL
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

**gemeinde**  
*(string) (optional)*

**ort**  
*(string) (optional)*

**ortsteil**  
*(string) (optional)*

**service**  
*(string) (optional)*

**abfall**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: c_trace_de
      args:
        ort: Bremen
        strasse: "Abbentorstra\xDFe"
        hausnummer: 5
```

## How to get the source arguments

'service' selects your operator (e.g. 'landau', 'augsburglandkreis'); leave it empty only if 'ort' is 'Bremen'. 'abfall' is a pipe-separated list of waste-type ids (e.g. '0|1|2|5') to restrict which types are fetched; leave it empty to fetch all types. Visit your provider's calendar page to see which ids correspond to which waste types.
