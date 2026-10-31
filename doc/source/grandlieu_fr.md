# Grand Lieu Communauté

Support for schedules provided by [Grand Lieu Communauté](https://www.grandlieu.fr).

Collection calendars for Geneston and five other Grand Lieu communes.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grandlieu_fr
      args:
        municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: grandlieu_fr
      args:
        municipality: Geneston
```

## How to get the source arguments

Select your commune. This source supports the shared six-commune calendar for Le Bignon, Geneston, La Limouzinière, Montbert, Saint Colomban and Saint Lumine de Coutais. Grey and yellow bins use the same dates. Public-holiday collections move to the Saturday specified by the calendar. Other communes and special drop-off events use separate calendars and are not included.
