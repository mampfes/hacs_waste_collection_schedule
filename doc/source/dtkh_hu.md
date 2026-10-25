# DTKH Nonprofit Kft.

Support for schedules provided by [DTKH Nonprofit Kft.](https://dtkh.hu).

Source for the waste collection calendars of the settlements served by DTKH.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dtkh_hu
      args:
        city: CITY
        district: DISTRICT
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**district**  
*(string) (optional)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: dtkh_hu
      args:
        city: "\xC1gasegyh\xE1za"
```

## How to get the source arguments

Enter your settlement as listed at https://dtkh.hu/telepules, e.g. "Kiskunfélegyháza". Where the yearly calendar (Hulladéknaptár) prints one table per collection weekday or per area, also enter yours as district: the weekday your general waste (vegyes hulladék) is collected (Hétfő = Monday, Kedd = Tuesday, Szerda = Wednesday, Csütörtök = Thursday, Péntek = Friday; either name works), or the area as printed, e.g. "Lakitelek - üdülő"; a wrong or missing district lists the possible ones. Towns that print a green-waste street list (Zöld utcajegyzék, e.g. Kiskunfélegyháza) collect green waste by street: enter your street as printed there, e.g. "Petőfi Sándor utca", or the full entry where a street is split by house numbers ("Nádasdy utca 1-5, 2-10"); leave it empty to skip green waste. Not supported: calendars without the month table (Kecskemét, Szeged, Kalocsa, Mindszent) or with a misprinted one (Kiskunhalas, Sándorfalva, Újszentiván), and Úri, whose calendar is not a PDF.
