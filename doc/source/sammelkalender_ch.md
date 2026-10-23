# Sammelkalender.ch

Support for schedules provided by [Sammelkalender.ch](https://info.sammelkalender.ch).

Source for Sammelkalender.ch.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sammelkalender_ch
      args:
        service_provider: SERVICE_PROVIDER
        municipality: MUNICIPALITY
        street: STREET
        hnr: HNR
```

### Configuration Variables

**service_provider**  
*(string) (required)*

**municipality**  
*(string) (required)*

**street**  
*(string) (optional)*

**hnr**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sammelkalender_ch
      args:
        service_provider: zeba
        municipality: Baar
        street: Aberenrain
        hnr: 10
```

## How to get the source arguments

Choose the waste association (`service_provider`) and enter your municipality as the association's calendar writes it. A municipality divided by street also needs `street` (and `hnr` for long streets); one divided into collection areas needs the area's name or abbreviation as `street`. The error message lists the valid values.
