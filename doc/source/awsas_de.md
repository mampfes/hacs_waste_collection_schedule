# AW SAS Burgenlandkreis

Support for schedules provided by [AW SAS](https://www.awsas.de), serving Burgenlandkreis, Saxony-Anhalt, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awsas_de
      args:
        municipality: MUNICIPALITY
        district: DISTRICT
```

### Configuration Variables

**municipality**
*(string) (required)*

Name of the municipality (Gemeinde/Stadt), e.g. `Gemeinde Elsteraue` or `Stadt Naumburg`.

**district**
*(string) (required)*

Name of the district (Ortsteil), e.g. `Langendorf`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awsas_de
      args:
        municipality: Gemeinde Elsteraue
        district: Langendorf
```

## How to get the source arguments

1. Go to <https://www.awsas.de/service/abfallkalender.html>.
2. Select your **Gemeinde/Stadt** from the first dropdown — this is the `municipality` value.
3. Select your **Ortsteil** from the second dropdown — this is the `district` value.

Use the names exactly as shown in the dropdowns (including prefixes like `Gemeinde` or `Stadt`).
