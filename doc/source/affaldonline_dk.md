# Affaldonline

Support for schedules from Affaldonline, which serves several Danish municipalities.
Upgraded to use the newer undocumented API, which most municipalities now use.

The source can be setup using configuration.yaml
But it is highly suggested to use the config flow instead, as the source can find the correct affaldonline **values** by simply selecting your street name and housenumber.

## Configuration via configuration.yaml
_Not recommended!_
```yaml
waste_collection_schedule:
    sources:
        - name: affaldonline_dk
          args:
              municipality: "favrskov"
              split_bins: False,
              values: "Nørregade|1||||8382|Hinnerup|6443|108156|0"
```

### Configuration Variables

**municipality**  
_(String) (required)_

The municipality of the app. The following are supported:

- aeroe
- assens
- favrskov
- fanoe
- fredericia
- ffv
- holbaek
- langeland
- middelfart
- morsoe
- nyborg
- rebild
- silkeborg
- vejle
- viborg
- 
**split_bins**  
_(Boolean) (optional)_

If True, the collections will be split into separate collections for every fraction that collection contains.

**values**  
_(String) (required)_

A string that includes the street name, house number, postal code, city name, and some numbers that seems to be internal affaldonline references. 

## How to find the "values" string to use

**Please consider using the config flow instead, as this is then handled for you**

Go to the Affaldonline site for your municipality: 

- [Ærø](https://www.affaldonline.dk/kalender/aeroe/)
- [Assens](https://www.affaldonline.dk/kalender/assens/)
- [Favrskov](https://www.affaldonline.dk/kalender/favrskov/)
- [Fanø](https://www.affaldonline.dk/kalender/fanoe/)
- [Fredericia](https://www.affaldonline.dk/kalender/fredericia/)
- [Faaborg (ffv)](https://www.affaldonline.dk/kalender/ffv/)
- [Holbæk](https://www.affaldonline.dk/kalender/holbaek/)
- [Langeland](https://www.affaldonline.dk/kalender/langeland/)
- [Middelfart](https://www.affaldonline.dk/kalender/middelfart/)
- [Morsø](https://www.affaldonline.dk/kalender/morsoe/)
- [Nyborg](https://www.affaldonline.dk/kalender/nyborg/)
- [Rebild](https://www.affaldonline.dk/kalender/rebild/)
- [Silkeborg](https://www.affaldonline.dk/kalender/silkeborg/)
- [Vejle](https://www.affaldonline.dk/kalender/vejle/)
- [Viborg (Revas)](https://www.affaldonline.dk/kalender/viborg/)

Open the developer console in your browser.

Enter your address and select the house number in the dropdown menu.

In the Network tab in the browser console, select the latest URL ending in **showInfo.php** and look under Payload, where you should find the **values** variable ready for copy/paste.

Depending on your browser, it should also be possible to right-click the house number field, and select "Inspect" - this should give you the html for the field, and here you can select the value from your house number in the list.