# GVA Baden

```diff
-This source is now depreciated
``````
**GVA Baden is now supported as part of the [Die NÖ Umweltverbände](/doc/source/umweltverbaende_at.md) source.**

<br>

## Legacy Information


Support for waste collection services Association of Municipalities in the District of Baden for [GVA Baden](https://baden.umweltverbaende.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: baden_umweltverbaende_at
      args:
        region: REGION

```

### Configuration Variables

**REGION**  
*(string) (required)*

The region for which the collection schedule is required. The region should be spelt as it appears on the [Abholtermine](https://baden.umweltverbaende.at/?kat=32) page. There is no need to include the "Marktgemeinde", "Gemeinde", or "Stadtgeminde" text.


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: baden_umweltverbaende_at
      args:
        region: "Mitterndorf an der Fischa"
```

