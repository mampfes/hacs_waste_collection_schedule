# Esch sur Alzette

Support for the Esch sur Alzette communal website in Luxembourg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: esch_lu
      args:
        zone: A
```

### Configuration Variables

There is currently only one conficuration variable, which is *zone*, which accepts only two chars - A or B.

**zone**
*(char) (required)*

This variable indicates collection zone. The city is divided by two zones with different collection schedule.
One can identify their zone prior to configuring here:
<https://administration.esch.lu/dechets/>

## Sensor setup

There are following types of garbage parsed:

- Poubelle ménage
- Papier
- Organique
- Verre
- Valorlux
- Déchets toxiques
- Container ménage