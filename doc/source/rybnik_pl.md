# Rybnik

Support for schedules provided by [Rybnik](https://www.rybnik.eu).

Source for Rybnik (Poland) municipal waste collection schedules provided by EKO Sp. z o.o.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rybnik_pl
      args:
        district: DISTRICT
        sub_district: SUB_DISTRICT
        property_type: PROPERTY_TYPE
        street: STREET
```

### Configuration Variables

**district**  
*(string) (optional)*

**sub_district**  
*(string) (optional)*

**property_type**  
*(string) (optional)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rybnik_pl
      args:
        district: Paruszowiec / Kamien
        sub_district: Paruszowiec-Piaski
        property_type: residential
```

## How to get the source arguments

Choose the property type: 'residential' (zamieszkałe), 'commercial' (firmy/niezamieszkałe) or 'multifamily' (zabudowa wielorodzinna). For residential and commercial properties enter the district group (e.g. 'Paruszowiec / Kamien') and optionally the Rejon (zone) from the left column of the PDF cover table (e.g. 'Kamień 1'); leave it blank for all zones of the district. The PDFs are on https://www.rybnik.eu/dla-mieszkancow/odpady-komunalne/. For multifamily housing enter your street as listed in the 'ULICE' column, and the 'DZIELNICA' value (e.g. 'Stodoły') as sub-district if the street is listed for several areas.
