# Umweltprofis.at

Support for schedules provided by [Umweltprofis.at](https://www.umweltprofis.at).

## Prerequisites

You need to generate your personal iCal Link before you can start using this source. Go to [https://data.umweltprofis.at/opendata/AppointmentService/index.aspx](https://data.umweltprofis.at/opendata/AppointmentService/index.aspx) and fill out the form. At the end, you can generate an iCal link. Copy this link and paste it to configuration.yaml as seen below.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_umweltprofis_at
      args:
        url: https://data.umweltprofis.at/OpenData/AppointmentService/AppointmentService.asmx/GetIcalWastePickupCalendar?key=xxx
      customize:
        - type: "Abholung: Hausabfall"
          alias: Restmüll
        - type: "Abholung: Gelbe Tonne"
          alias: Gelbe Tonne
        - type: "Abholung: Papiertonne"
          alias: Papier
        - type: "Abholung: Biotonne"
          alias: Biotonne
          show: false
```

### Configuration Variables

**url**<br>
*(url) (required)*