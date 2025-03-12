import json
import re
import time
import urllib.parse

import requests

if __name__ == "__main__":
    import os
    import sys

    sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))


from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions

SERVICE_MAP = [
    {
        "title": "Absdorf",
        "url": "https://www.absdorf.gv.at",
        "country": "at",
    },
    {
        "title": "Altenmarkt an der Triesting",
        "url": "https://www.altenmarkt-triesting.gv.at",
        "country": "at",
    },
    {
        "title": "Andau",
        "url": "https://www.andau-gemeinde.at",
        "country": "at",
    },
    {
        "title": "Andrichsfurt",
        "url": "https://www.andrichsfurt.at",
        "country": "at",
    },
    {
        "title": "Apetlon",
        "url": "https://gemeinde-apetlon.at",
        "country": "at",
    },
    {
        "title": "Arnfels",
        "url": "https://www.arnfels.gv.at",
        "country": "at",
    },
    {
        "title": "Bad Blumau",
        "url": "https://bad-blumau-gemeinde.at",
        "country": "at",
    },
    {
        "title": "Bad Fischau-Brunn",
        "url": "https://www.bad-fischau-brunn.at",
        "country": "at",
    },
    {
        "title": "Bad Gleichenberg",
        "url": "http://www.bad-gleichenberg.gv.at",
        "country": "at",
    },
    {
        "title": "Bad Loipersdorf",
        "url": "https://gemeinde.loipersdorf.at",
        "country": "at",
    },
    {
        "title": "Bad Radkersburg",
        "url": "https://www.bad-radkersburg.gv.at",
        "country": "at",
    },
    {
        "title": "Bad Schallerbach",
        "url": "https://www.bad-schallerbach.at",
        "country": "at",
    },
    {
        "title": "Bad Tatzmannsdorf",
        "url": "http://www.bad-tatzmannsdorf.at",
        "country": "at",
    },
    {
        "title": "Bad Waltersdorf",
        "url": "www.bad-waltersdorf.gv.at/home/",
        "country": "at",
    },
    {
        "title": "Baumgartenberg",
        "url": "https://baumgartenberg.at",
        "country": "at",
    },
    {
        "title": "Behamberg",
        "url": "behamberg.gv.at/",
        "country": "at",
    },
    {
        "title": "Bernstein",
        "url": "http://www.bernstein.gv.at",
        "country": "at",
    },
    {
        "title": "Bildein",
        "url": "http://www.bildein.at",
        "country": "at",
    },
    {
        "title": "Birkfeld",
        "url": "http://www.birkfeld.at",
        "country": "at",
    },
    {
        "title": "Blindenmarkt",
        "url": "blindenmarkt.gv.at/",
        "country": "at",
    },
    {
        "title": "Breitenbrunn am Neusiedler See",
        "url": "http://www.breitenbrunn.at",
        "country": "at",
    },
    {
        "title": "Breitenstein",
        "url": "https://www.breitenstein.at",
        "country": "at",
    },
    {
        "title": "Bromberg",
        "url": "http://www.bromberg.at",
        "country": "at",
    },
    {
        "title": "Bruckneudorf",
        "url": "http://www.bruckneudorf.eu",
        "country": "at",
    },
    {
        "title": "Buch - St. Magdalena",
        "url": "http://www.buch-stmagdalena.at",
        "country": "at",
    },
    {
        "title": "Burgau",
        "url": "https://www.burgau.info",
        "country": "at",
    },
    {
        "title": "Burgauberg-Neudauberg",
        "url": "http://www.burgauberg-neudauberg.at",
        "country": "at",
    },
    {
        "title": "Burgschleinitz-Kühnring",
        "url": "https://burgschleinitz-kuehnring.at",
        "country": "at",
    },
    {
        "title": "Bürg-Vöstenhof",
        "url": "http://www.buerg-voestenhof.at",
        "country": "at",
    },
    {
        "title": "Dechantskirchen",
        "url": "https://dechantskirchen.gv.at",
        "country": "at",
    },
    {
        "title": "Deutsch Goritz",
        "url": "https://www.deutsch-goritz.at",
        "country": "at",
    },
    {
        "title": "Deutsch Jahrndorf",
        "url": "https://www.deutsch-jahrndorf.at",
        "country": "at",
    },
    {
        "title": "Deutsch Kaltenbrunn",
        "url": "https://www.deutschkaltenbrunn.eu",
        "country": "at",
    },
    {
        "title": "Deutschkreutz",
        "url": "https://www.deutschkreutz.at",
        "country": "at",
    },
    {
        "title": "Dobl-Zwaring",
        "url": "https://www.dobl-zwaring.gv.at",
        "country": "at",
    },
    {
        "title": "Drasenhofen",
        "url": "https://www.drasenhofen.at",
        "country": "at",
    },
    {
        "title": "Draßmarkt",
        "url": "http://www.drassmarkt.at",
        "country": "at",
    },
    {
        "title": "Eberau",
        "url": "https://eberau.riskommunal.net",
        "country": "at",
    },
    {
        "title": "Eberndorf",
        "url": "https://www.eberndorf.at",
        "country": "at",
    },
    {
        "title": "Ebersdorf",
        "url": "https://www.ebersdorf.eu",
        "country": "at",
    },
    {
        "title": "Eberstein",
        "url": "https://www.eberstein.at",
        "country": "at",
    },
    {
        "title": "Edelsbach bei Feldbach",
        "url": "http://www.edelsbach.at",
        "country": "at",
    },
    {
        "title": "Eggenburg",
        "url": "www.eggenburg.gv.at/",
        "country": "at",
    },
    {
        "title": "Eggersdorf bei Graz",
        "url": "https://www.eggersdorf-graz.gv.at",
        "country": "at",
    },
    {
        "title": "Eichgraben",
        "url": "www.eichgraben.at/",
        "country": "at",
    },
    {
        "title": "Eisenstadt",
        "url": "https://www.eisenstadt.gv.at",
        "country": "at",
    },
    {
        "title": "Enzenreith",
        "url": "https://www.gemeinde-enzenreith.at",
        "country": "at",
    },
    {
        "title": "Fehring",
        "url": "http://www.fehring.at",
        "country": "at",
    },
    {
        "title": "Feistritz ob Bleiburg",
        "url": "https://feistritz-bleiburg.gv.at",
        "country": "at",
    },
    {
        "title": "Feistritztal",
        "url": "https://www.feistritztal.at",
        "country": "at",
    },
    {
        "title": "Feldbach",
        "url": "https://www.feldbach.gv.at",
        "country": "at",
    },
    {
        "title": "Feldkirchen in Kärnten",
        "url": "https://www.feldkirchen.at",
        "country": "at",
    },
    {
        "title": "Ferndorf",
        "url": "https://www.ferndorf.gv.at",
        "country": "at",
    },
    {
        "title": "Frankenau-Unterpullendorf",
        "url": "https://www.frankenau-unterpullendorf.gv.at",
        "country": "at",
    },
    {
        "title": "Frankenfels",
        "url": "www.frankenfels.at/",
        "country": "at",
    },
    {
        "title": "Frantschach - Sankt Gertraud",
        "url": "https://frantschach.gv.at",
        "country": "at",
    },
    {
        "title": "Frastanz",
        "url": "https://frastanz.at",
        "country": "at",
    },
    {
        "title": "Frauenkirchen",
        "url": "https://www.frauenkirchen.at",
        "country": "at",
    },
    {
        "title": "Fraxern",
        "url": "https://www.fraxern.at",
        "country": "at",
    },
    {
        "title": "Freistadt",
        "url": "https://www.freistadt.at",
        "country": "at",
    },
    {
        "title": "Fresach",
        "url": "https://fresach.gv.at",
        "country": "at",
    },
    {
        "title": "Friedberg",
        "url": "https://www.friedberg.gv.at",
        "country": "at",
    },
    {
        "title": "Friesach",
        "url": "https://friesach.gv.at",
        "country": "at",
    },
    {
        "title": "Frohnleiten",
        "url": "https://www.frohnleiten.com",
        "country": "at",
    },
    {
        "title": "Fürstenfeld",
        "url": "https://www.fuerstenfeld.gv.at",
        "country": "at",
    },
    {
        "title": "Gabersdorf",
        "url": "https://www.gabersdorf.gv.at",
        "country": "at",
    },
    {
        "title": "Gablitz",
        "url": "https://gablitz.at",
        "country": "at",
    },
    {
        "title": "Gattendorf",
        "url": "https://www.gattendorf.at",
        "country": "at",
    },
    {
        "title": "Gemeinde Sulz",
        "url": "https://www.gemeinde-sulz.at",
        "country": "at",
    },
    {
        "title": "Gersdorf an der Feistritz",
        "url": "https://www.gersdorf.gv.at",
        "country": "at",
    },
    {
        "title": "Gitschtal",
        "url": "gitschtal.gv.at/",
        "country": "at",
    },
    {
        "title": "Gleisdorf",
        "url": "https://gleisdorf.at",
        "country": "at",
    },
    {
        "title": "Gols",
        "url": "https://www.gols.at",
        "country": "at",
    },
    {
        "title": "Grafendorf bei Hartberg",
        "url": "https://grafendorf.at",
        "country": "at",
    },
    {
        "title": "Grafenschachen",
        "url": "https://www.grafenschachen.at",
        "country": "at",
    },
    {
        "title": "Grafenstein",
        "url": "https://grafenstein.gv.at",
        "country": "at",
    },
    {
        "title": "Grafenwörth",
        "url": "https://www.grafenwoerth.at",
        "country": "at",
    },
    {
        "title": "Gratkorn",
        "url": "https://www.gratkorn.gv.at",
        "country": "at",
    },
    {
        "title": "Gratwein-Straßengel",
        "url": "https://gratwein-strassengel.gv.at",
        "country": "at",
    },
    {
        "title": "Greinbach",
        "url": "https://gemeinde-greinbach.at",
        "country": "at",
    },
    {
        "title": "Großsteinbach",
        "url": "www.gemeinde-grosssteinbach.at/",
        "country": "at",
    },
    {
        "title": "Großwarasdorf",
        "url": "https://www.grosswarasdorf.at",
        "country": "at",
    },
    {
        "title": "Großwilfersdorf",
        "url": "http://www.grosswilfersdorf.steiermark.at",
        "country": "at",
    },
    {
        "title": "Grödig",
        "url": "www.groedig.at/",
        "country": "at",
    },
    {
        "title": "Gutenberg",
        "url": "https://www.gutenberg-stenzengreith.gv.at",
        "country": "at",
    },
    {
        "title": "Güssing",
        "url": "https://www.guessing.co.at",
        "country": "at",
    },
    {
        "title": "Güttenbach",
        "url": "https://www.guettenbach.at",
        "country": "at",
    },
    {
        "title": "Haag am Hausruck",
        "url": "www.haag-hausruck.at/",
        "country": "at",
    },
    {
        "title": "Hagenberg im Mühlkreis",
        "url": "https://www.hagenberg.at",
        "country": "at",
    },
    {
        "title": "Hannersdorf",
        "url": "https://www.hannersdorf.at",
        "country": "at",
    },
    {
        "title": "Hartberg",
        "url": "https://www.hartberg.at",
        "country": "at",
    },
    {
        "title": "Heiligenkreuz",
        "url": "https://www.heiligenkreuz.at",
        "country": "at",
    },
    {
        "title": "Heiligenkreuz am Waasen",
        "url": "https://www.heiligenkreuz-waasen.gv.at",
        "country": "at",
    },
    {
        "title": "Heimschuh",
        "url": "https://www.heimschuh.at",
        "country": "at",
    },
    {
        "title": "Heldenberg",
        "url": "https://www.heldenberg.gv.at",
        "country": "at",
    },
    {
        "title": "Henndorf am Wallersee",
        "url": "www.henndorf.at/",
        "country": "at",
    },
    {
        "title": "Heugraben",
        "url": "www.heugraben.at/",
        "country": "at",
    },
    {
        "title": "Hirm",
        "url": "www.hirm.gv.at/",
        "country": "at",
    },
    {
        "title": "Hochwolkersdorf",
        "url": "https://www.hochwolkersdorf.at",
        "country": "at",
    },
    {
        "title": "Hofstätten an der Raab",
        "url": "https://www.hofstaetten.at",
        "country": "at",
    },
    {
        "title": "Horitschon",
        "url": "http://www.horitschon.at",
        "country": "at",
    },
    {
        "title": "Horn",
        "url": "https://horn.gv.at",
        "country": "at",
    },
    {
        "title": "Hornstein",
        "url": "https://www.hornstein.at",
        "country": "at",
    },
    {
        "title": "Hüttenberg",
        "url": "https://huettenberg.at",
        "country": "at",
    },
    {
        "title": "Ilz",
        "url": "https://www.ilz.at",
        "country": "at",
    },
    {
        "title": "Ilztal",
        "url": "https://www.ilztal.at",
        "country": "at",
    },
    {
        "title": "Inzenhof",
        "url": "https://www.inzenhof.at",
        "country": "at",
    },
    {
        "title": "Jabing",
        "url": "https://www.gemeinde-jabing.at",
        "country": "at",
    },
    {
        "title": "Jagerberg",
        "url": "http://www.jagerberg.info",
        "country": "at",
    },
    {
        "title": "Kaindorf",
        "url": "https://www.kaindorf.at",
        "country": "at",
    },
    {
        "title": "Kaisersdorf",
        "url": "http://www.kaisersdorf.com",
        "country": "at",
    },
    {
        "title": "Kalsdorf bei Graz",
        "url": "https://www.kalsdorf-graz.gv.at",
        "country": "at",
    },
    {
        "title": "Kapfenstein",
        "url": "http://www.kapfenstein.at",
        "country": "at",
    },
    {
        "title": "Kemeten",
        "url": "https://www.kemeten.gv.at",
        "country": "at",
    },
    {
        "title": "Kirchbach-Zerlach",
        "url": "www.kirchbach-zerlach.at/",
        "country": "at",
    },
    {
        "title": "Kirchberg am Wagram",
        "url": "https://www.kirchberg-wagram.at",
        "country": "at",
    },
    {
        "title": "Kirchberg an der Raab",
        "url": "https://www.kirchberg-raab.gv.at",
        "country": "at",
    },
    {
        "title": "Kittsee",
        "url": "https://www.kittsee.at",
        "country": "at",
    },
    {
        "title": "Klaus",
        "url": "https://www.klaus.at",
        "country": "at",
    },
    {
        "title": "Kleinmürbisch",
        "url": "https://www.kleinmürbisch.at",
        "country": "at",
    },
    {
        "title": "Klingenbach",
        "url": "https://klingenbach.at",
        "country": "at",
    },
    {
        "title": "Klöch",
        "url": "https://www.kloech.com",
        "country": "at",
    },
    {
        "title": "Kobersdorf",
        "url": "www.kobersdorf.at/index.php",
        "country": "at",
    },
    {
        "title": "Kohfidisch",
        "url": "http://www.kohfidisch.at",
        "country": "at",
    },
    {
        "title": "Korneuburg",
        "url": "https://www.korneuburg.gv.at",
        "country": "at",
    },
    {
        "title": "Kötschach-Mauthen",
        "url": "https://koetschach-mauthen.gv.at",
        "country": "at",
    },
    {
        "title": "Krensdorf",
        "url": "https://www.krensdorf.at",
        "country": "at",
    },
    {
        "title": "Krieglach",
        "url": "https://www.krieglach.at",
        "country": "at",
    },
    {
        "title": "Kuchl",
        "url": "www.kuchl.net/",
        "country": "at",
    },
    {
        "title": "Laa an der Thaya",
        "url": "http://www.laa.at",
        "country": "at",
    },
    {
        "title": "Lackenbach",
        "url": "https://www.gemeinde-lackenbach.at",
        "country": "at",
    },
    {
        "title": "Lackendorf",
        "url": "https://www.lackendorf.at",
        "country": "at",
    },
    {
        "title": "Langau",
        "url": "http://www.langau.at",
        "country": "at",
    },
    {
        "title": "Langenrohr",
        "url": "https://www.langenrohr.gv.at",
        "country": "at",
    },
    {
        "title": "Langenzersdorf",
        "url": "www.langenzersdorf.gv.at/",
        "country": "at",
    },
    {
        "title": "Leibnitz",
        "url": "https://www.leibnitz.at",
        "country": "at",
    },
    {
        "title": "Leithaprodersdorf",
        "url": "http://www.leithaprodersdorf.at",
        "country": "at",
    },
    {
        "title": "Leutschach an der Weinstraße",
        "url": "https://www.leutschach-weinstrasse.gv.at",
        "country": "at",
    },
    {
        "title": "Lieboch",
        "url": "https://www.lieboch.gv.at",
        "country": "at",
    },
    {
        "title": "Litzelsdorf",
        "url": "https://www.litzelsdorf.at",
        "country": "at",
    },
    {
        "title": "Lockenhaus",
        "url": "www.lockenhaus.at/",
        "country": "at",
    },
    {
        "title": "Loipersbach im Burgenland",
        "url": "https://www.loipersbach.info",
        "country": "at",
    },
    {
        "title": "Ludersdorf - Wilfersdorf",
        "url": "https://www.lu-wi.at",
        "country": "at",
    },
    {
        "title": "Lurnfeld",
        "url": "https://lurnfeld.gv.at",
        "country": "at",
    },
    {
        "title": "Mariasdorf",
        "url": "https://www.mariasdorf.at",
        "country": "at",
    },
    {
        "title": "Markt Allhau",
        "url": "https://www.marktallhau.gv.at",
        "country": "at",
    },
    {
        "title": "Markt Hartmannsdorf",
        "url": "https://www.markthartmannsdorf.at",
        "country": "at",
    },
    {
        "title": "Markt Neuhodis",
        "url": "http://www.markt-neuhodis.at",
        "country": "at",
    },
    {
        "title": "Markt Piesting-Dreistetten",
        "url": "https://www.piesting.at",
        "country": "at",
    },
    {
        "title": "Marz",
        "url": "https://www.marz.gv.at",
        "country": "at",
    },
    {
        "title": "Mattersburg",
        "url": "https://www.mattersburg.gv.at",
        "country": "at",
    },
    {
        "title": "Meiningen",
        "url": "https://www.meiningen.at",
        "country": "at",
    },
    {
        "title": "Meiseldorf",
        "url": "https://www.meiseldorf.gv.at",
        "country": "at",
    },
    {
        "title": "Melk",
        "url": "https://www.stadt-melk.at",
        "country": "at",
    },
    {
        "title": "Mettersdorf am Saßbach",
        "url": "http://www.mettersdorf.com",
        "country": "at",
    },
    {
        "title": "Miesenbach",
        "url": "https://www.miesenbach.at",
        "country": "at",
    },
    {
        "title": "Mischendorf",
        "url": "https://www.mischendorf.at",
        "country": "at",
    },
    {
        "title": "Mistelbach",
        "url": "https://www.mistelbach.at",
        "country": "at",
    },
    {
        "title": "Mitterdorf an der Raab",
        "url": "https://www.mitterdorf-raab.at",
        "country": "at",
    },
    {
        "title": "Moosburg",
        "url": "www.moosburg.gv.at",
        "country": "at",
    },
    {
        "title": "Mönchhof",
        "url": "https://www.moenchhof.at",
        "country": "at",
    },
    {
        "title": "Mörbisch am See",
        "url": "https://moerbisch.gv.at",
        "country": "at",
    },
    {
        "title": "Mureck",
        "url": "https://www.mureck.gv.at",
        "country": "at",
    },
    {
        "title": "Neudau",
        "url": "https://www.neudau.gv.at",
        "country": "at",
    },
    {
        "title": "Neudorf bei Parndorf",
        "url": "http://www.neudorfbeiparndorf.at",
        "country": "at",
    },
    {
        "title": "Neudörfl",
        "url": "https://www.neudoerfl.gv.at",
        "country": "at",
    },
    {
        "title": "Neufeld an der Leitha",
        "url": "https://www.neufeld-leitha.at",
        "country": "at",
    },
    {
        "title": "Neusiedl am See",
        "url": "https://www.neusiedlamsee.at",
        "country": "at",
    },
    {
        "title": "Neustift bei Güssing",
        "url": "http://www.xn--neustift-bei-gssing-jbc.at",
        "country": "at",
    },
    {
        "title": "Nickelsdorf",
        "url": "https://www.nickelsdorf.gv.at",
        "country": "at",
    },
    {
        "title": "Niederneukirchen",
        "url": "https://www.niederneukirchen.ooe.gv.at",
        "country": "at",
    },
    {
        "title": "Ober-Grafendorf",
        "url": "https://gemeinde.ober-grafendorf.gv.at",
        "country": "at",
    },
    {
        "title": "Oberpullendorf",
        "url": "https://www.oberpullendorf.gv.at",
        "country": "at",
    },
    {
        "title": "Oberschützen",
        "url": "https://www.oberschuetzen.at",
        "country": "at",
    },
    {
        "title": "Oberwart",
        "url": "https://www.oberwart.gv.at",
        "country": "at",
    },
    {
        "title": "Oslip",
        "url": "http://www.oslip.at",
        "country": "at",
    },
    {
        "title": "Ottendorf an der Rittschein",
        "url": "https://www.ottendorf-rittschein.steiermark.at",
        "country": "at",
    },
    {
        "title": "Paldau",
        "url": "http://www.paldau.gv.at",
        "country": "at",
    },
    {
        "title": "Pama",
        "url": "https://www.gemeinde-pama.at",
        "country": "at",
    },
    {
        "title": "Pamhagen",
        "url": "https://www.gemeinde-pamhagen.at",
        "country": "at",
    },
    {
        "title": "Parndorf",
        "url": "http://www.gemeinde-parndorf.at",
        "country": "at",
    },
    {
        "title": "Payerbach",
        "url": "https://www.payerbach.at",
        "country": "at",
    },
    {
        "title": "Peggau",
        "url": "https://peggau.at",
        "country": "at",
    },
    {
        "title": "Pernegg an der Mur",
        "url": "http://pernegg.at",
        "country": "at",
    },
    {
        "title": "Pernegg im Waldviertel",
        "url": "https://www.pernegg.info",
        "country": "at",
    },
    {
        "title": "Perschling",
        "url": "www.perschling.at/",
        "country": "at",
    },
    {
        "title": "Pfarrwerfen",
        "url": "http://www.gemeinde.pfarrwerfen.at",
        "country": "at",
    },
    {
        "title": "Pilgersdorf",
        "url": "https://www.pilgersdorf.at",
        "country": "at",
    },
    {
        "title": "Pinggau",
        "url": "https://www.pinggau.gv.at",
        "country": "at",
    },
    {
        "title": "Pinkafeld",
        "url": "https://www.pinkafeld.gv.at",
        "country": "at",
    },
    {
        "title": "Pischelsdorf am Kulm",
        "url": "https://www.pischelsdorf.com",
        "country": "at",
    },
    {
        "title": "Podersdorf am See",
        "url": "http://www.gemeindepodersdorfamsee.at",
        "country": "at",
    },
    {
        "title": "Poggersdorf",
        "url": "https://gemeinde-poggersdorf.at",
        "country": "at",
    },
    {
        "title": "Pottenstein",
        "url": "www.pottenstein.at/",
        "country": "at",
    },
    {
        "title": "Potzneusiedl",
        "url": "https://www.potzneusiedl.at",
        "country": "at",
    },
    {
        "title": "Poysdorf",
        "url": "https://www.poysdorf.at",
        "country": "at",
    },
    {
        "title": "Pöchlarn",
        "url": "https://www.poechlarn.at",
        "country": "at",
    },
    {
        "title": "Pregarten",
        "url": "www.pregarten.at/",
        "country": "at",
    },
    {
        "title": "Premstätten",
        "url": "www.premstaetten.gv.at/",
        "country": "at",
    },
    {
        "title": "Prigglitz",
        "url": "https://prigglitz.at",
        "country": "at",
    },
    {
        "title": "Raach am Hochgebirge",
        "url": "https://www.raach.at",
        "country": "at",
    },
    {
        "title": "Raasdorf",
        "url": "www.raasdorf.gv.at/",
        "country": "at",
    },
    {
        "title": "Radmer",
        "url": "https://www.radmer.at",
        "country": "at",
    },
    {
        "title": "Ragnitz",
        "url": "https://www.ragnitz.gv.at",
        "country": "at",
    },
    {
        "title": "Raiding",
        "url": "https://www.raiding-online.at",
        "country": "at",
    },
    {
        "title": "Rechnitz",
        "url": "www.rechnitz.at/de/",
        "country": "at",
    },
    {
        "title": "Reichenau",
        "url": "https://reichenau.gv.at",
        "country": "at",
    },
    {
        "title": "Reichenau an der Rax",
        "url": "https://www.reichenau.at",
        "country": "at",
    },
    {
        "title": "Rettenegg",
        "url": "https://www.rettenegg.at",
        "country": "at",
    },
    {
        "title": "Rohr bei Hartberg",
        "url": "https://www.rohr-bei-hartberg.at",
        "country": "at",
    },
    {
        "title": "Rohr im Burgenland",
        "url": "www.rohr-bgld.at/",
        "country": "at",
    },
    {
        "title": "Rottenbach",
        "url": "https://www.rottenbach.gv.at",
        "country": "at",
    },
    {
        "title": "Röthis",
        "url": "https://www.roethis.at",
        "country": "at",
    },
    {
        "title": "Rudersdorf",
        "url": "http://www.rudersdorf.at",
        "country": "at",
    },
    {
        "title": "Rust",
        "url": "https://www.freistadt-rust.at",
        "country": "at",
    },
    {
        "title": "Saalfelden am Steinernen Meer",
        "url": "www.stadtmarketing-saalfelden.at/de",
        "country": "at",
    },
    {
        "title": "Sankt Georgen an der Stiefing",
        "url": "https://www.st-georgen-stiefing.gv.at",
        "country": "at",
    },
    {
        "title": "Sankt Gilgen",
        "url": "https://www.gemgilgen.at",
        "country": "at",
    },
    {
        "title": "Sankt Oswald bei Plankenwarth",
        "url": "https://www.sanktoswald.net",
        "country": "at",
    },
    {
        "title": "Schäffern",
        "url": "https://www.schaeffern.gv.at",
        "country": "at",
    },
    {
        "title": "Schlins",
        "url": "https://www.schlins.at",
        "country": "at",
    },
    {
        "title": "Schrattenberg",
        "url": "https://www.schrattenberg.gv.at",
        "country": "at",
    },
    {
        "title": "Schützen am Gebirge",
        "url": "https://www.schuetzen-am-gebirge.at",
        "country": "at",
    },
    {
        "title": "Schwadorf",
        "url": "https://www.schwadorf.gv.at",
        "country": "at",
    },
    {
        "title": "Schwarzenbach an der Pielach",
        "url": "https://www.schwarzenbach-pielach.at",
        "country": "at",
    },
    {
        "title": "Seiersberg-Pirka",
        "url": "https://www.gemeindekurier.at",
        "country": "at",
    },
    {
        "title": "Siegendorf",
        "url": "https://www.siegendorf.gv.at",
        "country": "at",
    },
    {
        "title": "Sieggraben",
        "url": "https://www.sieggraben.at",
        "country": "at",
    },
    {
        "title": "Sigleß",
        "url": "https://www.sigless.at",
        "country": "at",
    },
    {
        "title": "Sigmundsherberg",
        "url": "https://www.sigmundsherberg.gv.at",
        "country": "at",
    },
    {
        "title": "Silbertal",
        "url": "https://www.silbertal.eu",
        "country": "at",
    },
    {
        "title": "Sinabelkirchen",
        "url": "https://www.sinabelkirchen.eu",
        "country": "at",
    },
    {
        "title": "Söchau",
        "url": "http://www.soechau.steiermark.at",
        "country": "at",
    },
    {
        "title": "St. Andrä",
        "url": "https://www.st-andrae.gv.at",
        "country": "at",
    },
    {
        "title": "St. Andrä am Zicksee",
        "url": "https://www.gemeinde-standrae.at",
        "country": "at",
    },
    {
        "title": "St. Anna am Aigen",
        "url": "http://www.st-anna-aigen.gv.at",
        "country": "at",
    },
    {
        "title": "St. Egyden am Steinfeld",
        "url": "https://www.st-egyden.at",
        "country": "at",
    },
    {
        "title": "St. Florian bei Linz",
        "url": "www.st-florian.at/",
        "country": "at",
    },
    {
        "title": "St. Georgen an der Leys",
        "url": "www.stgeorgenleys.at/",
        "country": "at",
    },
    {
        "title": "St. Jakob im Rosental",
        "url": "www.st-jakob-rosental.gv.at/",
        "country": "at",
    },
    {
        "title": "St. Johann in der Haide",
        "url": "http://www.st-johann-haide.gv.at",
        "country": "at",
    },
    {
        "title": "St. Konrad",
        "url": "www.st-konrad.at/",
        "country": "at",
    },
    {
        "title": "St. Lorenzen am Wechsel",
        "url": "https://www.st-lorenzen-wechsel.at",
        "country": "at",
    },
    {
        "title": "St. Margarethen an der Raab",
        "url": "https://www.st-margarethen-raab.at",
        "country": "at",
    },
    {
        "title": "St. Margarethen im Burgenland",
        "url": "https://www.st-margarethen.at",
        "country": "at",
    },
    {
        "title": "St. Martin im Innkreis",
        "url": "https://www.st-martin-innkreis.ooe.gv.at",
        "country": "at",
    },
    {
        "title": "St. Peter - Freienstein",
        "url": "https://www.st-peter-freienstein.gv.at",
        "country": "at",
    },
    {
        "title": "St. Peter am Ottersbach",
        "url": "http://www.st-peter-ottersbach.gv.at",
        "country": "at",
    },
    {
        "title": "St. Radegund bei Graz",
        "url": "https://www.radegund.info",
        "country": "at",
    },
    {
        "title": "St. Ruprecht an der Raab",
        "url": "https://www.st.ruprecht.at",
        "country": "at",
    },
    {
        "title": "St. Urban",
        "url": "https://sturban.at",
        "country": "at",
    },
    {
        "title": "St. Veit in der Südsteiermark",
        "url": "https://www.st-veit-suedsteiermark.gv.at",
        "country": "at",
    },
    {
        "title": "Statzendorf",
        "url": "https://statzendorf.at",
        "country": "at",
    },
    {
        "title": "Stegersbach",
        "url": "https://gemeinde.stegersbach.at",
        "country": "at",
    },
    {
        "title": "Steinbrunn",
        "url": "https://www.steinbrunn.at",
        "country": "at",
    },
    {
        "title": "Steuerberg",
        "url": "https://www.steuerberg.at",
        "country": "at",
    },
    {
        "title": "Stinatz",
        "url": "http://www.stinatz.gv.at",
        "country": "at",
    },
    {
        "title": "Stiwoll",
        "url": "https://www.stiwoll.at",
        "country": "at",
    },
    {
        "title": "Stockerau",
        "url": "http://www.stockerau.at",
        "country": "at",
    },
    {
        "title": "Stössing",
        "url": "https://www.stoessing.gv.at",
        "country": "at",
    },
    {
        "title": "Straden",
        "url": "https://www.straden.gv.at",
        "country": "at",
    },
    {
        "title": "Straß in Steiermark",
        "url": "https://www.strass-steiermark.gv.at",
        "country": "at",
    },
    {
        "title": "Stubenberg",
        "url": "https://www.stubenberg.gv.at",
        "country": "at",
    },
    {
        "title": "Tadten",
        "url": "https://www.tadten.at",
        "country": "at",
    },
    {
        "title": "Tattendorf",
        "url": "https://www.tattendorf.at",
        "country": "at",
    },
    {
        "title": "Taufkirchen an der Trattnach",
        "url": "www.taufkirchen.at/home",
        "country": "at",
    },
    {
        "title": "Thal",
        "url": "https://thal.gv.at",
        "country": "at",
    },
    {
        "title": "Tieschen",
        "url": "https://www.tieschen.gv.at",
        "country": "at",
    },
    {
        "title": "Tobaj",
        "url": "http://www.tobaj.gv.at",
        "country": "at",
    },
    {
        "title": "Tragöß - St. Katharein",
        "url": "https://www.tragoess-st-katharein.gv.at",
        "country": "at",
    },
    {
        "title": "Trofaiach",
        "url": "https://www.trofaiach.gv.at",
        "country": "at",
    },
    {
        "title": "Tulln an der Donau",
        "url": "https://www.tulln.at",
        "country": "at",
    },
    {
        "title": "Unterfrauenhaid",
        "url": "https://www.unterfrauenhaid.at",
        "country": "at",
    },
    {
        "title": "Unterkohlstätten",
        "url": "https://www.unterkohlstaetten.at",
        "country": "at",
    },
    {
        "title": "Unterlamm",
        "url": "http://www.unterlamm.gv.at",
        "country": "at",
    },
    {
        "title": "Unterwart",
        "url": "https://www.unterwart.at",
        "country": "at",
    },
    {
        "title": "Übelbach",
        "url": "https://www.uebelbach.gv.at",
        "country": "at",
    },
    {
        "title": "Vasoldsberg",
        "url": "https://www.vasoldsberg.gv.at",
        "country": "at",
    },
    {
        "title": "Viktorsberg",
        "url": "https://www.viktorsberg.at",
        "country": "at",
    },
    {
        "title": "Villach",
        "url": "villach.at/",
        "country": "at",
    },
    {
        "title": "Vordernberg",
        "url": "http://www.vordernberg.steiermark.at",
        "country": "at",
    },
    {
        "title": "Vorderstoder",
        "url": "www.vorderstoder.ooe.gv.at/",
        "country": "at",
    },
    {
        "title": "Völkermarkt",
        "url": "https://voelkermarkt.gv.at",
        "country": "at",
    },
    {
        "title": "Waidhofen an der Thaya",
        "url": "https://www.waidhofen-thaya.at",
        "country": "at",
    },
    {
        "title": "Walpersbach",
        "url": "http://www.walpersbach.gv.at",
        "country": "at",
    },
    {
        "title": "Wartberg ob der Aist",
        "url": "www.wartberg-aist.at/",
        "country": "at",
    },
    {
        "title": "Weiden am See",
        "url": "https://www.weiden-see.at",
        "country": "at",
    },
    {
        "title": "Weißenkirchen in der Wachau",
        "url": "https://www.weissenkirchen-wachau.at",
        "country": "at",
    },
    {
        "title": "Weitersfeld",
        "url": "https://www.weitersfeld.gv.at",
        "country": "at",
    },
    {
        "title": "Weiz",
        "url": "https://www.weiz.at",
        "country": "at",
    },
    {
        "title": "Weppersdorf",
        "url": "https://www.weppersdorf.at",
        "country": "at",
    },
    {
        "title": "Werfenweng",
        "url": "http://www.gemeinde-werfenweng.at",
        "country": "at",
    },
    {
        "title": "Werndorf",
        "url": "https://werndorf.gv.at",
        "country": "at",
    },
    {
        "title": "Wies",
        "url": "https://www.wies.at",
        "country": "at",
    },
    {
        "title": "Wiesen",
        "url": "https://www.wiesen.eu",
        "country": "at",
    },
    {
        "title": "Wiesfleck",
        "url": "https://www.gemeinde-wiesfleck.at",
        "country": "at",
    },
    {
        "title": "Wiesmath",
        "url": "http://www.wiesmath.at",
        "country": "at",
    },
    {
        "title": "Wimpassing an der Leitha",
        "url": "http://www.wimpassing-leitha.at",
        "country": "at",
    },
    {
        "title": "Winden am See",
        "url": "https://www.winden.at",
        "country": "at",
    },
    {
        "title": "Winklarn",
        "url": "winklarn.gv.at/",
        "country": "at",
    },
    {
        "title": "Wolfau",
        "url": "https://www.gemeinde-wolfau.at",
        "country": "at",
    },
    {
        "title": "Wolfsberg",
        "url": "https://www.wolfsberg.at",
        "country": "at",
    },
    {
        "title": "Wolkersdorf im Weinviertel",
        "url": "http://www.wolkersdorf.at",
        "country": "at",
    },
    {
        "title": "Wörterberg",
        "url": "http://www.woerterberg.at",
        "country": "at",
    },
    {
        "title": "Wulkaprodersdorf",
        "url": "https://www.wulkaprodersdorf.at",
        "country": "at",
    },
    {
        "title": "Zagersdorf",
        "url": "http://www.zagersdorf.at",
        "country": "at",
    },
    {
        "title": "Zelking-Matzleinsdorf",
        "url": "http://www.zelking-matzleinsdorf.gv.at",
        "country": "at",
    },
    {
        "title": "Zillingtal",
        "url": "https://www.zillingtal.eu",
        "country": "at",
    },
    {
        "title": "Zurndorf",
        "url": "https://zurndorf.at",
        "country": "at",
    },
    {
        "title": "Zwischenwasser",
        "url": "https://www.zwischenwasser.at",
        "country": "at",
    },
]


class CitiesApps:
    def __init__(self, password, email=None, phone=None) -> None:
        if (email is None and phone is None) or password is None:
            raise Exception("(email or phone) and password required")
        if email is not None and phone is not None:
            raise Exception("Only provide one of email or phone not both")

        # get authentication
        self._session = requests.Session()
        self._session.headers.update(
            {
                "user-agent": "cities/100.100.100/Android",
                "requesting-app": "user-android",
            }
        )

        username = phone if email is None else email
        r = self._session.post(
            "https://api.v2.citiesapps.com/auth",
            json={
                "method": "email" if email is not None else "phoneNumber",
                "emailOrPhoneNumber": username,
                "password": password,
            },
        )
        if r.status_code == 400:
            raise Exception("failed to login to the App, check your login credentials")
        r.raise_for_status()

        self._session.headers.update({"authorization": r.headers["access-token"]})

    def get_cities(self) -> list:
        cities = []
        next_url = "/cities?pagination=limit:100"
        while next_url:
            r = self._session.get("https://api.v2.citiesapps.com" + next_url)
            r.raise_for_status()
            j = r.json()
            next_url = j["nextUrl"]
            cities += j["data"]
        return cities

    def get_specific_citiy(self, search: str) -> dict:
        cities = self.get_cities()
        for city in cities:
            if city["name"].lower().strip() == search.lower().strip():
                return city
        raise SourceArgumentNotFoundWithSuggestions(
            "city", search, [city["name"] for city in cities]
        )

    def get_uses_garbage_calendar_v2(self, city_id: str) -> bool:
        r = self._session.get(f"https://api.citiesapps.com/entities/{city_id}/services")
        r.raise_for_status()
        essentials = r.json()["essentials"]

        return essentials["garbage_calendar_v2"]

    def fetch_garbage_plans(self, city: str, calendar: str):
        city_dict = self.get_specific_citiy(city)
        api: CitiesApps.GarbageApiV2 | CitiesApps.GarbageApiV1 = (
            CitiesApps.GarbageApiV1(self._session)
        )
        is_v2 = self.get_uses_garbage_calendar_v2(city_dict["_id"])

        if is_v2:
            api = CitiesApps.GarbageApiV2(self._session)

        return {"is_v2": is_v2, "data": api.fetch_garbage_plans(city_dict, calendar)}

    def get_garbage_calendars(self, city_id: str) -> dict[str, bool | list]:
        api: CitiesApps.GarbageApiV2 | CitiesApps.GarbageApiV1 = self.GarbageApiV1(
            self._session
        )
        is_v2 = self.get_uses_garbage_calendar_v2(city_id)

        if is_v2:
            api = CitiesApps.GarbageApiV2(self._session)

        return {"is_v2": is_v2, "data": api.get_garbage_calendars(city_id)}

    def get_supported_cities(self) -> dict[str, list]:
        supported_dict: dict[str, list] = {"supported": [], "not_supported": []}
        cities = self.get_cities()
        print(f"fetching cities: {len(cities)}")
        for idx, city in enumerate(cities):
            if (idx % 10) == 0:
                print(f"{idx}/{len(cities)}")
            if self.get_garbage_calendars(city["_id"]):
                supported_dict["supported"].append(city)
            else:
                supported_dict["not_supported"].append(city)
        return supported_dict

    def get_city_home_page(self, city):
        city_page_id = city["cityPage"]["_id"]
        r = self._session.get(
            f"https://api.v2.citiesapps.com/pages/{city_page_id}?include=tabBar"
        )
        r.raise_for_status()
        j = r.json()
        if "website" not in j:
            if city["name"] in SERVICE_MAP:
                return SERVICE_MAP[city["name"]]
            return ""
        if j["website"] is None:
            print(f"website for city {city['name']} is None, fill in manually")
        return j["website"]

    def generate_service_map(self) -> list[dict[str, str]]:
        supported_dict = self.get_supported_cities()
        if len(supported_dict["not_supported"]) > 0:
            print(
                "# not supported: ",
                len(supported_dict["not_supported"]),
                ":",
                supported_dict["not_supported"],
            )
        service_map = []

        supported_len = len(supported_dict["supported"])
        for id, city in enumerate(supported_dict["supported"]):
            if city["name"] in [c["title"] for c in SERVICE_MAP]:
                city_homepage = [
                    c["url"] for c in SERVICE_MAP if city["name"] == c["title"]
                ][0]
            else:
                print(f"{id + 1}/{supported_len} {city['name']}")
                city_homepage = self.get_city_home_page(city)
            if city_homepage is not None:
                slash_index = [m.start() for m in re.finditer("/", city_homepage)]
                domain_end = (
                    slash_index[2] if len(slash_index) > 2 else len(city_homepage)
                )
                url = city_homepage[:domain_end]
            else:
                url = None
            # city["country_abbreviation"] returns "de" instead of "at" sometimes
            service_map.append({"title": city["name"], "url": url, "country": "at"})
        return service_map

    class GarbageApiV1:
        def __init__(self, session: requests.Session) -> None:
            self._session = session

        def fetch_garbage_plans(self, city_dict: dict, calendar: str):
            city_id = city_dict["_id"]
            specific_calendar = self.get_specific_calendar(city_id, calendar)

            return self.get_garbage_plans(specific_calendar)

        def get_specific_calendar(self, city_id: str, search: str) -> dict:
            calendars = self.get_garbage_calendars(city_id)
            for calendar in calendars:
                if calendar["name"].lower().strip() == search.lower().strip():
                    return calendar
            raise SourceArgumentNotFoundWithSuggestions(
                "calendar", search, [calendar["name"] for calendar in calendars]
            )

        def get_garbage_plans(self, garbage_calendar: dict) -> list:
            r = self._session.get(
                "https://api.citiesapps.com/garbagecalendars/",
                params={"full": "true", "ids": garbage_calendar["_id"]},
            )
            r.raise_for_status()
            garbage_plans = []
            for cal in r.json():
                garbage_plans += cal["garbage_plans"]
            return garbage_plans

        def get_garbage_calendars(self, city_id: str) -> list:
            params = {
                "filter": json.dumps(
                    {"entityid": {"$in": [city_id]}}, separators=(",", ":")
                ),
            }
            params_str = urllib.parse.urlencode(params, safe=":$")

            r = self._session.get(
                "https://api.citiesapps.com/garbagecalendars/filter", params=params_str
            )
            r.raise_for_status()
            return r.json()["garbage_calendars"]

    class GarbageApiV2:
        def __init__(self, session: requests.Session) -> None:
            self._session = session

        def fetch_garbage_plans(self, city_dict: dict, calendar: str):
            city_id = city_dict["_id"]
            specific_calendar = self.get_specific_calendar(city_id, calendar)

            return self.get_garbage_plans(specific_calendar)

        def get_specific_calendar(self, city_id: str, search: str) -> dict:
            calendars = self.get_garbage_calendars_with_search(city_id, search)
            for calendar in calendars:
                if calendar["street"].lower().strip() == search.lower().strip():
                    return calendar

            suggestions = [calendar["street"] for calendar in calendars]

            if len(suggestions) == 0:
                suggestions = [
                    "Recheck your CitiesApp, the name of the calendar might have changed"
                ]

            raise SourceArgumentNotFoundWithSuggestions("calendar", search, suggestions)

        def get_garbage_plans(self, garbage_calendar: dict) -> list:
            r = self._session.get(
                f"https://api.v2.citiesapps.com/waste-management/areas/{garbage_calendar['_id']}/calendar"
            )
            r.raise_for_status()

            return r.json()["garbageCollectionDays"]

        def get_garbage_calendars_with_search(self, city_id: str, search: str) -> list:
            r = self._session.get(
                f"https://api.v2.citiesapps.com/waste-management/by-city/{city_id}/areas/search/autocomplete?query={search}&limit=100"
            )
            r.raise_for_status()
            return r.json()["garbageAreas"]

        def get_garbage_calendars(self, city_id: str) -> list:
            calendars = []
            next_url = f"/waste-management/by-city/{city_id}/areas?pagination=limit:100"

            while next_url:
                time.sleep(0.1)
                r = self._session.get(f"https://api.v2.citiesapps.com/{next_url}")
                try:
                    r.raise_for_status()
                except requests.exceptions.HTTPError as e:
                    if r.status_code == 429:
                        time.sleep(3)
                        continue
                    raise e

                j = r.json()
                next_url = j["nextUrl"]
                calendars += j["data"]

            r.raise_for_status()
            return calendars


if __name__ == "__main__":
    c = CitiesApps(email=input("email: "), password=input("password: "))
    service_map = c.generate_service_map()
    service_map_copy = SERVICE_MAP.copy()

    print("[")
    for service in service_map:
        print(4 * " " + "{")
        for key, value in service.items():
            print(8 * " " + f'"{key}": "{value}",')
        print(4 * " " + "},")
    print("]")

    print("\nchanges to the service map:")
    for new_service in service_map:
        found = False
        for service in SERVICE_MAP:
            if new_service["title"] == service["title"]:
                if service["url"] != new_service["url"]:
                    print(
                        f"{new_service['title']}: {service['url']} -> {new_service['url']}"
                    )
                found = True
                service_map_copy.remove(service)
                break
        if not found:
            print(f"new service: {new_service['title']}: {new_service['url']}")
    for service in service_map_copy:
        print(f"service removed: {service['title']}: {service['url']}")
