# SiUnet

Support for waste collection calendars published on the SiUnet platform (`differenziati.siunet.it`) by Greenext, serving 320 municipalities across Italy under various local branded apps (e.g. [Esacom](https://www.esacom.it) for the Verona area).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: siunet_it
      args:
        comune: ZEVIO
        zona: Zona Rossa
```

### Configuration Variables

**comune**
*(string) (required)*

Name of the municipality, exactly as listed in the "Supported municipalities" section below. Two pairs of entries share the same name because the municipality switched waste-management provider at some point; both are kept, suffixed `(1)`/`(2)` — try the other one if your municipality doesn't return results.

**zona**
*(string) (optional)*

For municipalities whose collections are split by zone (e.g. `Zona Rossa` / `Zona Verde`), the zone to filter for. Collections that are not zone-specific are always included. Leave empty if your municipality has no zones.

## How to get the arguments

1. Find your municipality in the "Supported municipalities" list below and copy its exact spelling.
2. If your municipality has zones, look up the zone name from your local waste-management provider's calendar (e.g. Esacom for the Verona area) or from your last paper calendar.

## Supported municipalities

- Abbadia Lariana (1)
- Abbadia Lariana (2)
- Agrate Brianza
- Aicurzio
- Airuno
- Albiate
- Albosaggia
- Alessano
- Alezio
- Alliste
- Altavilla Vicentina
- Andora
- Andria
- Angiari
- Annone Di Brianza
- Anzola Dell'Emilia
- Apricena
- Arconate
- Arcore
- Arrone
- Ballabio
- Barlassina
- Barzago
- Barzanò
- Barzio
- Basiano
- Basiglio
- Belfiore
- Bellano
- Bellinzago Lombardo
- Bellusco
- Bernareggio
- Besana In Brianza
- Bevilacqua
- Biassono
- Binasco
- Boffalora Sopra Ticino
- Bolzano Vicentino
- Borgo San Giovanni
- Bosisio Parini
- Bovisio Masciago
- Bovolone
- Bressanvido
- Briosco
- Brivio
- Brugherio
- Bulciago
- Burago Di Molgora
- Buscate
- Busnago
- Bussero
- Cabiate
- Calco
- Caldogno
- Calolziocorte
- Calvi Dell'Umbria
- Cambiago
- Camisano Vicentino
- Camparada
- Canegrate
- Caponago
- Carate Brianza
- Carenno
- Carnate
- Carovigno
- Carpiano
- Carugate
- Casaleone
- Casaletto Lodigiano
- Casalmaiocco
- Casargo
- Casarile
- Casatenovo
- Caselle Lurani
- Cassago Brianza
- Cassano D'Adda
- Cassina De' Pecchi
- Cassina Valsassina
- Castagnaro
- Castegnero
- Castellanza
- Castello Di Brianza
- Cavenago Di Brianza
- Ceriano Laghetto
- Cernusco Lombardone
- Cernusco Sul Naviglio
- Cerro Al Lambro
- Cervignano D'Adda
- Cervo
- Cesana Brianza
- Cesano Maderno
- Cesio
- Chiusanico
- Cisternino
- Civate
- Cogliate
- Colico
- Colle Brianza
- Cologno Monzese
- Colturano
- Comazzo
- Concamarise
- Concorezzo
- Cornaredo
- Cornate D'Adda
- Correzzana
- Cortenova
- Costa Masnaga
- Crandola Valsassina
- Cremella
- Cremeno
- Cuggiono
- Cusano Milanino
- Dairago
- Dervio
- Desio
- Diano Arentino
- Diano Castello
- Diano Marina
- Diano San Pietro
- Dolzago
- Dorio
- Dresano
- Dueville
- Ello
- Erbè
- Erve
- Esino Lario
- Fasano
- Ferentillo
- Gaggiano
- Galbiate
- Gallarate
- Gallipoli
- Garbagnate Monastero
- Garlate
- Gazzo Veronese
- Genova
- Gessate
- Giussano
- Gorgonzola
- Grezzago
- Grisignano Di Zocco
- Grumolo Delle Abbadesse
- Gudo Visconti
- Imbersago
- Introbio
- Inzago
- Ischitella
- Isola Della Scala
- Isola Rizza
- Isola Vicentina
- La Valletta Brianza
- Lasnigo
- Lecco
- Legnano
- Lesina
- Lesmo
- Lierna
- Limbiate
- Liscate
- Lissone
- Locate Di Triulzi
- Lomagna
- Longare
- Macherio
- Magenta
- Magnago
- Malgrate
- Mandello Del Lario
- Manduria
- Marcallo Con Casone
- Margherita Di Savoia
- Margno
- Martignano
- Martina Franca
- Masate
- Massalengo
- Mediglia
- Melegnano
- Melissano
- Melzo
- Merate
- Merlino
- Mezzago
- Misinto
- Missaglia
- Moggio
- Molteno
- Monte Marenzo
- Montecchio Precalcino
- Montefranco
- Montegalda
- Montegaldella
- Montevecchia
- Monticello Brianza
- Monticello Conte Otto
- Morciano Di Leuca
- Morterone
- Mulazzano
- Narni
- Nibionno
- Nogara
- Nogarole Rocca
- Nova Milanese
- Noviglio
- Oggiono
- Olgiate Molgora
- Olginate
- Oliveto Lario
- Oppeano
- Ornago
- Osnago
- Ossona
- Paderno D'Adda
- Pagnona
- Palù
- Pantigliate
- Parabiago
- Parlasco
- Pasturo
- Paullo
- Perledo
- Pescate
- Pessano Con Bornago
- Pieve Emanuele
- Poggiardo
- Polino
- Pozzo D'Adda
- Pozzuolo Martesana
- Premana
- Primaluna
- Pusiano
- Quinto Vicentino
- Racale
- Renate (1)
- Renate (2)
- Rescaldina
- Rivolta D'Adda
- Robbiate
- Robecchetto Con Induno
- Rodano
- Rogeno
- Rognano
- Roncello
- Ronco All'Adige
- Ronco Briantino
- Rosate
- Rovello Porro
- Roverchiara
- Salerano Sul Lambro
- Salizzole
- Salve
- San Bartolomeo Al Mare
- San Ferdinando Di Puglia
- San Giorgio Su Legnano
- San Giovanni Lupatoto
- San Pietro Di Morubio
- San Zenone Al Lambro
- Sandrigo
- Sannicandro Garganico
- Sant'Angelo Lodigiano
- Santa Maria Hoè
- Seregno
- Settala
- Seveso
- Sirone
- Sirtori
- Solbiate Olona
- Sondrio
- Sordio
- Sorgà
- Sovico
- Stellanello
- Sueglio
- Suello
- Sulbiate
- Taceno
- Taviano
- Terni
- Terrazzo
- Testico
- Tiggiano
- Torre De' Busi
- Torrevecchia Pia
- Torri Di Quartesolo
- Trevenzuolo
- Treviglio
- Trezzano Rosa
- Trezzo Sull'Adda
- Tribiano
- Tricase
- Triuggio
- Truccazzano
- Turbigo
- Usmate Velate
- Valgreghentino
- Valmadrera
- Valvarrone
- Vaprio D'Adda
- Varedo
- Varenna
- Vedano Al Lambro
- Veduggio Con Colzano
- Verano Brianza
- Vercurago
- Verderio
- Vernate
- Viganò
- Vigasio
- Vignate
- Villa Cortese
- Villa Faraldi
- Villasanta
- Vimercate (1)
- Vimercate (2)
- Vimodrone
- Vizzolo Predabissi
- Zevio
- Zibido San Giacomo

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: siunet_it
      args:
        comune: San Giovanni Lupatoto
```
