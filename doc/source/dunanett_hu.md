# Dunanett Nonprofit Kft.

Support for schedules provided by [Dunanett Nonprofit Kft.](https://www.dunanett.hu).

Source for Dunanett waste calendars in five Hungarian municipalities.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dunanett_hu
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
    - name: dunanett_hu
      args:
        municipality: Pusztaszabolcs
```

## How to get the source arguments

Select one municipality: Pusztaszabolcs, Rácalmás, Perkáta, Nagyvenyim or Dunaföldvár. Official publication indices are https://pusztaszabolcs.hu/, https://racalmas.hu/category/hirek/, https://perkata.munipolis.hu/p/hulladekszallitas, https://nagyvenyim.hu/ and https://dunafoldvar.hu/hir-kategoria/hulladekokkal-kapcsolatos-informaciok/. The provider is https://www.dunanett.hu. The source discovers annual PDF, HTML or DOCX calendars for current/future years automatically, uses the latest timestamped PDF upload or the uniquely published link, and fails on ambiguous links or if the current year is unavailable rather than reusing an expired calendar. New calendars may only be published in January, so the source can be unavailable at the start of the year until publication.

General waste, recycling and garden waste are included, except in Dunaföldvár: its document publishes only recycling and garden dates, so no general-waste schedule is returned there. Where the calendar restricts January collections to Christmas trees, those events use the Garden Waste category with a tree-only description: remove decorations and other waste; ordinary garden waste is not accepted. Bulky waste is by appointment and has no calendar dates. Permanent glass drop-off points are not dated collections.

These are the annual planned dates. Ad-hoc weather cancellations or street-specific replacement notices are not included; check municipal news and https://www.dunanett.hu/nonprofit/hireink/. Other Dunanett municipalities are not supported: current machine-readable annual calendars could not be verified, or the available calendars are image-only.
