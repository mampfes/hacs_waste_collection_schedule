# Potsdam

Support for schedules provided by [Potsdam](https://www.potsdam.de).

Source for Potsdam.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: potsdam_de
      args:
        ortsteil: ORTSTEIL
        strasse: STRASSE
        rest_rhythm: REST_RHYTHM
        papier_rhythm: PAPIER_RHYTHM
        bio_rhythm: BIO_RHYTHM
        gelb_rhythm: GELB_RHYTHM
```

### Configuration Variables

**ortsteil**  
*(string) (required)*

**strasse**  
*(string) (required)*

**rest_rhythm**  
*(string) (optional)*

**papier_rhythm**  
*(string) (optional)*

**bio_rhythm**  
*(string) (optional)*

**gelb_rhythm**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: potsdam_de
      args:
        ortsteil: Golm
        strasse: Akazienweg
        rest_rhythm: 4
        papier_rhythm: 2
        bio_rhythm: 3
```

## How to get the source arguments

District and street as in the Potsdam waste calendar. The rhythms match the choice in the calendar for general waste, organic waste and paper: 1 = twice a week, 2 = weekly, 3 = every two weeks, 4 = every four weeks; organic waste also 5 = combined emptying.
