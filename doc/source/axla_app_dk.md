# Axla Affaldonline Apps

Support for schedules from Axla's Affaldonline apps, which serves several Danish municipalities.

Each municipality have their own flavour of the app, but the underlying api is the same.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
        - name: axla_app_dk
          args:
              municipality: "assens"
              addressid: "430000"
```

### Configuration Variables

**municipality**  
_(String) (required)_

The municipality of the app. The following are supported:
- aeroe 
- assens
- favrskov
- ffv
- holbaek
- langeland
- morsoe
- rebild
- vejle
- viborg

**addressid**  
_(String) (required)_

The addressid associated with your home. You need to find this using your municipality website. Look below for how to.

## How to find the "addressid" for your home

Go to the Affaldonline site for your municipality: 

- [Ærø](https://www.affaldonline.dk/kalender/aeroe/)
- [Assens](https://www.affaldonline.dk/kalender/assens/)
- [Favrskov](https://www.affaldonline.dk/kalender/favrskov/)
- [Faaborg (FFV)](https://www.affaldonline.dk/kalender/ffv/)
- [Holbæk (Fors)](https://www.affaldonline.dk/kalender/holbaek/)
- [Langeland](https://www.affaldonline.dk/kalender/langeland/)
- [Morsø](https://www.affaldonline.dk/kalender/morsoe/)
- [Rebild](https://www.affaldonline.dk/kalender/rebild/)
- [Vejle](https://www.affaldonline.dk/kalender/vejle/)
- [Viborg (Revas)](https://www.affaldonline.dk/kalender/viborg/)

Open the developer console in your browser.

Enter your address and select the house number in the dropdown menu.

In the Network tab in the browser console, select the latest URL ending in **showInfo.php** and look under Payload, where you should find the **values** variable. The address ID is the last non zero number.

For example in Faaborg with the address Østergade 1 in Faaborg the **values** variable would be: Østergade|1||||5600|Faaborg|40910294|**13118**|0

The address ID in this example would be **13118**.

Depending on your browser, it should also be possible to right-click the house number field, and select "Inspect" - this should give you the html for the field, and here you can select the value from your house number in the list.