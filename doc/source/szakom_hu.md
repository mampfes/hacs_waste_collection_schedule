# Szákom (Százhalombatta)

Support for schedules listed by [Szákom](https://www.szakom.hu), serving Százhalombatta, HU.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: szakom_hu
      args:
        area_communal: AREA_COMMUNAL
        area_recycle: AREA_RECYCLE
        area_green: AREA_GREEN
```

### Configuration Variables

**AREA_COMMUNAL**
*(string) (required)*
- Lakótelep | hétfő, szerda, péntek
- Családi házas | kedd
- Családi házas | kedd, péntek

**AREA_RECYCLE**
*(string) (required)*
- Damjanich u.-Benta patak közötti rész, Óváros | csütörtök
- Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | csütörtök

**AREA_GREEN**
*(string) (required)*
- Damjanich u.-Benta patak közötti rész | hétfő
- Damjanich u.-Csónakház közötti rész, Újtelep, Urbárium | szerda
- Óváros | csütörtök

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: szakom_hu
      args:
        area_communal: Családi házas | kedd, péntek
        area_recycle: Damjanich u.-Benta patak közötti rész, Óváros | csütörtök
        area_green: Óváros | csütörtök
```