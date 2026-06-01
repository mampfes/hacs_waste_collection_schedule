# Monteco Spa

Support for schedules provided by [Monteco Spa](https://www.montecospa.it), serving 26 municipalities in Puglia and Basilicata, Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: montecospa_it
      args:
        municipality: Lecce
        zone: zona_centro_storico
```

### Configuration Variables

**municipality**
*(string) (required)*

Name of the municipality exactly as listed on the Monteco website (e.g. `Lecce`).

**zone**
*(string) (required)*

Zone name as shown in the URL/map on the Monteco website (e.g. `zona_centro_storico`). Use underscores, not spaces.

**user_type**
*(string) (optional, default: `Domestica`)*

User type. One of `Domestica` (residential) or `Non domestica` (non-residential/commercial).

## How to get the arguments

1. Open [https://www.montecospa.it/it/servizi-evoluti?cta=calendario](https://www.montecospa.it/it/servizi-evoluti?cta=calendario).
2. Click on your address on the map.
3. Note the **municipality** and **zone** shown in the results panel.
4. Use those values as the `municipality` and `zone` arguments.

## Supported municipalities

- Alberobello
- Campi Salentina
- Carosino
- Casalabate
- Corigliano d'Otranto
- Crispiano
- Cursi
- Erchie
- Francavilla Fontana
- Guagnano
- Latiano
- Lecce
- Locorotondo
- Martina Franca
- Novoli
- Oria
- Palagianello
- Salice Salentino
- San Michele Salentino
- San Pancrazio Salentino
- Sogliano Cavour
- Squinzano
- Statte
- Surbo
- Torre Santa Susanna
- Trepuzzi

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: montecospa_it
      args:
        municipality: Lecce
        zone: zona_centro_storico
        user_type: Domestica
```
