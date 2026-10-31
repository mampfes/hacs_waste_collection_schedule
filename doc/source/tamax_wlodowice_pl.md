# TAMAX (Gmina Włodowice)

Support for schedules provided by [TAMAX (Gmina Włodowice)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Włodowice.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_wlodowice_pl
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_wlodowice_pl
      args:
        area: "W\u0142odowice (bez ul. Kopaniny, R\xF3\u017Cana i Leszczynowa), Morsko"
```

## How to get the source arguments

Find Gmina Włodowice (mieszkańcy) at https://www.tamax.net.pl/harmonogramy/. Select your exact village group, including the street exceptions in Włodowice and Rudniki. Use Trudne wjazdy only if the council assigned your property to that route. Yellow cells collect mixed waste and bio. Red cells collect mixed waste and all listed segregated fractions, including recycling, bio and ash. Ash is Other with the original Popiół label. The dated bulky collection is also read from the PDF, even though it is operated separately by Przedsiębiorstwo Komunalne Ogrodzieniec. Collection-centre opening days (PSZOK), apartment-block and business schedules are not household collection events.
