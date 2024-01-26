# Insert IT Apps

Support Apps provided by [Insert IT](https://insert-it.de/). The official homepage is using the URL [Insert Infotech](https://insert-infotech.de/) instead.

```yaml
waste_collection_schedule:
  sources:
    - name: insert_it_de
      args:
        municipality: Municipality
        street: Street Name
        hnr: House Number
        location_id: Location ID
```

### Configuration Variables

**municipality**  
*(string) (required)*

**street**  
*(string) (optional)*

**hnr**  
*(integer) (optional)*

**location_id**  
*(integer) (optional)*


Either `street` and `hnr` or `location_id` is required. Both could also be set, but `location_id` is prioritized.
If none is set, it will fail.


Currently supported municipalities:

|Region|
|-|
| Hattingen |
| Herne |
| Kassel |
| Krefeld |
| Luebeck |
| Mannheim |
| Offenbach |


## Example

Using Location ID
```yaml
waste_collection_schedule:
  sources:
    - name: insert_it_de
      args:
        municipality: Mannheim
        location_id: 430650
```

Using Street and House Number
```yaml
waste_collection_schedule:
  sources:
    - name: insert_it_de
      args:
        municipality: Offenbach
        street: Kaiserstraße
        hnr: 1
```


## How to get the source arguments

Easy way to get the `location_id` source argument is to use a (desktop) browser, eg.g Google Chrome:

1. Open the digital abfallkalender, e.g. for Offenbach [https://www.offenbach.de/stadtwerke/stadtservice/Entsorgung/abfallkalender.php](https://www.offenbach.de/stadtwerke/stadtservice/Entsorgung/abfallkalender.php).
2. Enter the street name and the number
3. Right click on the iCalendar link and select "Copy Link Address"
4. Paste somewhere like a notepad to get the full URL. Eg: https://www.insert-it.de/BmsAbfallkalenderOffenbach/Main/Calender?bmsLocationId=7036&year=2024
5. The bmsLocationId argument is the location id that you need to use in the configuration as `location_id`.
