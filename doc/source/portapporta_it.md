# PortAPPorta (ERSU, ASMIU, REA, ESA)

Support for schedules provided by [PortAPPorta (ERSU, ASMIU, REA, ESA)](https://portapporta.webmapp.it).

Source for the PortAPPorta app: ERSU (Versilia, Lunigiana), ASMIU (Massa), REA (Rosignano Marittimo, Cecina) and ESA (Elba).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: portapporta_it
      args:
        gestore: GESTORE
        comune: COMUNE
        zona: ZONA
        utenza: UTENZA
```

### Configuration Variables

**gestore**  
*(string) (required)*

**comune**  
*(string) (required)*

**zona**  
*(string) (optional)*

**utenza**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: portapporta_it
      args:
        gestore: rea
        comune: Rosignano Marittimo
        zona: Gabbro, Nibbiaia e Castelnuovo della Misericordia
```

## How to get the source arguments

Choose the operator: `ersu` (Versilia and Lunigiana), `asmiu` (Massa), `rea` (Rosignano Marittimo, Cecina and surroundings) or `esa` (Elba). Enter your comune as the PortAPPorta app lists it, e.g. `Rosignano Marittimo`. Where the comune has more than one collection zone, also enter the zone as named in the app, e.g. `Gabbro, Nibbiaia e Castelnuovo della Misericordia` (a wrong or missing zone lists the valid ones). The domestic calendar is used unless you enter another user type in `utenza`, e.g. `Commerciale`.
