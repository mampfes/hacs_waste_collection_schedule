# Gmina Żukowo (ELWOZ ECO)

Support for schedules provided by [Gmina Żukowo (ELWOZ ECO)](https://elwozeco.pl).

Source for Gmina Żukowo (ELWOZ ECO) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: elwozeco_pl
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: elwozeco_pl
      args:
        district: Skrzeszewo
```

## How to get the source arguments

ELWOZ ECO publishes the Gmina Żukowo household calendars at https://elwozeco.pl/harmonogram/ (one PDF per sector). Enter the village name as printed, for example Skrzeszewo. In Żukowo and Banino the calendar is split by street: enter the street as printed, including the house-number range when the PDF shows one (each range is its own round). Żukowo on its own matches the numbered Żukowo zones and the multifamily (WIELORODZINNE) round, so the error lists those headings. The same happens for a name printed on more than one page, such as Barniewice or Dąbrowa. Przyjaźń on its own is the village calendar; multifamily buildings in Przyjaźń, Babi Dół and Żukowo use WIELORODZINNE. Business (Firmy) calendars are not included.
