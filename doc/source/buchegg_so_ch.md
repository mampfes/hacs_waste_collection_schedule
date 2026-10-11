# Buchegg

Support for schedules provided by [Buchegg](https://www.buchegg-so.ch).

Source for waste collection schedule of Gemeinde Buchegg (SO), Switzerland.

## Configuration via configuration.yaml

### Using locality

```yaml
waste_collection_schedule:
  sources:
    - name: buchegg_so_ch
      args:
        locality: LOCALITY
```

### Using ortschaft

```yaml
waste_collection_schedule:
  sources:
    - name: buchegg_so_ch
      args:
        ortschaft: ORTSCHAFT
```

### Configuration Variables

**locality**  
*(string) (alternative)*

**ortschaft**  
*(string) (alternative)*

Provide one of: `locality` or `ortschaft`.

## Example

### Using locality

```yaml
waste_collection_schedule:
  sources:
    - name: buchegg_so_ch
      args:
        locality: Aetingen
```

### Using ortschaft

```yaml
waste_collection_schedule:
  sources:
    - name: buchegg_so_ch
      args:
        ortschaft: Tscheppach
```

## How to get the source arguments

Select your village from the list. `ortschaft` is the deprecated name of `locality`.
