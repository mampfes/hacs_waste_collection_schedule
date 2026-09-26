# Gemeinde Hasselroth

Support for schedules provided by [Gemeinde Hasselroth](https://www.hasselroth.de).

Source for Gemeinde Hasselroth, Hesse, Germany waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hasselroth_de
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hasselroth_de
      args:
        district: Neuenhasslau
```

## How to get the source arguments

The Hasselroth district (Ortsteil), e.g. 'Neuenhasslau', 'Niedermittlau' or 'Gondsroth'.
