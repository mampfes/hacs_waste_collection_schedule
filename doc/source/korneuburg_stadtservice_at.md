# Abfallkalender der Gemeinde Korneuburg

Support for schedules provided by [Stadtservice Korneuburg](https://www.korneuburg.gv.at/Rathaus/Buergerservice/Muellabfuhr) located in Korneuburg, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: korneuburg_stadtservice_at
      args:
        street_name: Straßenname
        street_number: 1A
        teilgebiet: 1
```

### Configuration Variables

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

**teilgebiet**  
*(string) (optional)*

### How to get the source arguments

The arguments can be found on [Stadtservice Korneuburg](https://www.korneuburg.gv.at/Rathaus/Buergerservice/Muellabfuhr).

Check if your address details are available on the official site. If not use something that is close by or the same region.

You can enter your region number (`teilgebiet`) directly to skip the step that determines your region based on your address.
Still some values need to be set for `street_name` and `street_number` which are then not used.

## Example

**First Entry**

```yaml
waste_collection_schedule:
  sources:
    - name: korneuburg_stadtservice_at
      args:
        street_name: "Albrecht Dürer-Gasse"
        street_number: 2
```

**Rathaus**

```yaml
waste_collection_schedule:
  sources:
    - name: korneuburg_stadtservice_at
      args:
        street_name: Hauptplatz
        street_number: 39
```

**Rathaus using Teilgebiet**

```yaml
waste_collection_schedule:
  sources:
    - name: korneuburg_stadtservice_at
      args:
        street_name: Some Street
        street_number: 1A
        teilgebiet: 4
```
