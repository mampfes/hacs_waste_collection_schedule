from waste_collection_schedule.exceptions import (
    SourceArgumentNotFoundWithSuggestions,
    SourceArgumentRequiredWithSuggestions,
)
from waste_collection_schedule.service.junker_app import (
    AreaNotFound,
    AreaRequired,
    Junker,
)

TITLE = "Jnker APP"
DESCRIPTION = "Source for Jnker APP."
URL = "https://junker.app"
TEST_CASES = {"Val della torre": {"municipality": "Val della torre"}}

COUNTRY = "it"


SERVICE_PROVIDERS = {
    "Unione dei Comuni di Valmalenco",
    "Bubbiano",
    "Econova Srl",
    "Monserrato - Gesenu Spa",
    "Saluggia",
    "Ambiente Spa",
    "Laurenzana",
    "Trappeto",
    "Torpè - Eco Flap - Ciclat",
    "Buonvicino",
    "Chiaramonte Gulfi - Mecogest",
    "Valle Umbra Servizi S.p.A.",
    "Veritas Spa",
    "Anguillara Sabazia - Cosp Tecno Service",
    "Sezze - SPL",
    "Bitti, Luna e Onanì - Formula Ambiente Spa",
    "Trivento - Smaltimenti Sud",
    "Sala Consilina - SuperEco SRL",
    "Cesa - DM Technology Srl",
    "Inverno e Monteleone",
    "Rovellasca",
    "Ginosa",
    "Bientina",
    "Fondi - De Vizia Transfer Spa",
    "Dolomiti Ambiente Srl",
    "Gioiosa Ionica",
    "Sieco Spa",
    "Fiemme Servizi",
    "Caronno Pertusella - Econord",
    "Castelbuono - Castelbuono Ambiente srl",
    "Santa Lucia del Mela",
    "Rieco - Marche",
    "Prossedi",
    "Rosora",
    "Isola del Liri - Cosp Tecno Service",
    "Casale Marittimo",
    "Monteflavio, Montorio Romano, Moricone - Diodoro Ecologia",
    "Lavorgna Srl",
    "Itri - De Vizia Transfer Spa",
    "Quarto - DM Technology Srl",
    "Montefiascone - Viterbo Ambiente",
    "Sabaudia - Del Prete Srl",
    "Andora",
    "Wipptal",
    "Vasto - Pulchra Ambiente Srl",
    "Challand-Saint-Victor",
    "Massalengo",
    "Unione Comuni Terre del Campidano - Formula Ambiente Spa",
    "Villaricca - Sieco Spa",
    "Posada - Formula Ambiente Spa",
    "Gestione Ambiente Spa",
    "Bellunum Srl",
    "Paullo",
    "Chieti - Formula Ambiente Spa",
    "Lucca - Sistema Ambiente Spa",
    "Marcallo con Casone",
    "Priolo Gargallo -  IGM rifiuti industriali",
    "Unione Basso Biferno - Impregico Srl",
    "Borgomaro",
    "Cupello - Pulchra Ambiente Srl",
    "Cologno Monzese - CEM Ambiente",
    "Cisternino",
    "Latina - ABC Azienda Beni Comuni di Latina",
    "Rieti - ASM Rieti Spa",
    "Letino",
    "Floridia - IGM rifiuti industriali",
    "Valfornace",
    "Unione Comuni del Villanova - Formula Ambiente Spa",
    "Meda",
    "Cinisello Balsamo - Nord Milano Ambiente S.P.A.",
    "Campagnano di Roma  - DM Technology Srl",
    "Levate",
    "Terracina",
    "Pulsano - Al.ma. Ecologia Srl",
    "Maracalagonis - Formula Ambiente Spa",
    "Carini - Senesi SpA",
    "Fonni, Oliena e Orgosolo - San Germano - Gruppo Iren",
    "Monterotondo Marittimo",
    "Marsala, Trapani e Misiliscemi- Formula Ambiente Spa",
    "Casavatore - Ecology Srl",
    "Ispica - Impregico Srl",
    "Cerro Maggiore - Agesp Spa",
    "Entratico",
    "Co.S.R.A.B",
    "Imperia - De Vizia Transfer Spa",
    "Scanzorosciate",
    "Siniscola - DLR Ambiente - Ciclat",
    "Formula Ambiente Spa - Abruzzo",
    "GardaUno Spa",
    "Monticiano",
    "Bassano Romano",
    "Santa Maria Capua Vetere - DHI",
    "Lacco Ameno - SuperEco SRL",
    "Sammichele di Bari e Casamassima - Meridionale Servizi Ambientali srl",
    "Spoltore - Rieco",
    "Cisterna di Latina - Cisterna Ambiente",
    "Villaspeciosa",
    "Monteverdi Marittimo",
    "Mandas - C.A.P.R.I.",
    "Rescaldina",
    "Unione dei Comuni del Guilcier - Cosir Srl",
    "Lodi",
    "Ecoambiente Srl",
    "Aci Sant'Antonio",
    "Monterotondo - APM",
    "Comunità Valsugana e Tesino",
    "Palombara Sabina",
    "Muraca Srl",
    "Montalto di Castro",
    "Calatafimi Segesta",
    "Ravello",
    "Capua - CZETA Spa - Ciclat",
    "Campobasso - S.E.A. Servizi e Ambiente SPA",
    "Volsca Ambiente",
    "Calvi Risorta - Isola Verde Ecologia",
    "Tivoli - ASA Tivoli Spa",
    "Campolieto - Smaltimenti Sud",
    "Sanremo - Amaie Energia e Servizi Srl",
    "Solza",
    "Montescudaio",
    "Viagrande",
    "Potenza - Acta Spa",
    "Mondolfo",
    "CLARA Ambiente",
    "Terre Roveresche",
    "Auer - Ora",
    "Borgosesia - Seso Srl",
    "Agno Chiampo Ambiente",
    "Vezzano sul Crostolo",
    "Robecchetto con Induno",
    "Leinì",
    "Cosir Srl",
    "Saprodir",
    "Macerata Campania - DHI",
    "Comunità Montana Sarcidano e Barbagia di Seulo - Formula Ambiente Spa",
    "Gonnesa - De Vizia Transfer Spa",
    "Borghetto di Borbera",
    "Castiglione in Teverina - Cosp Tecno Service",
    "Rocca di Papa - DM Technology Srl",
    "Illasi",
    "Covar14",
    "Orciano Pisano",
    "Messina - Messinaservizi Bene Comune",
    "Mottola e Laterza - Meridionale Servizi Ambientali Srl",
    "Carrara - Nausicaa S.p.a",
    "Aset S.p.A",
    "Nuoro - È-Comune srl",
    "Riola Sardo - EffeAmbiente",
    "Limosano",
    "Acinque Spa",
    "Bagheria - A.M.B. S.p.a",
    "Brandizzo",
    "Monte Isola - Sea Srl",
    "AET Ambiente Energia Territorio S.p.A.",
    "Nicosia - Leukosia",
    "Decimoputzu - Formula Ambiente Spa",
    "Rieco - Lazio",
    "Giarre - IGM rifiuti industriali",
    "Bari - Amiu Puglia",
    "Miramare Service Srl",
    "Pimonte - Ecogin Srl",
    "Castellammare del Golfo - Agesp Spa",
    "Gavorrano",
    "Unione Comuni del Meilogu - Formula Ambiente Spa",
    "Castelforte",
    "Conca Casale e Venafro - Smaltimenti Sud",
    "Loreto Aprutino - Diodoro Ecologia",
    "Seab SPA Bolzano",
    "Riparbella",
    "Follonica",
    "Pomarance",
    "Aprilia - Progetto Ambiente Spa",
    "Castelnuovo di Porto",
    "Azienda Ambiente Srl",
    "DLR Ambiente - Ciclat",
    "Blera",
    "Pratola Peligna - Diodoro Ecologia",
    "Cesano Boscone - San Germano - Gruppo Iren",
    "Pescina - Pulchra Ambiente Srl",
    "GESENU  Gestione Servizi Nettezza Urbana S.P.A",
    "Montepulciano",
    "Canicattini Bagni - Traina Srl",
    "Vitulazio - DM Technology Srl",
    "Termoli - Rieco Sud Scarl",
    "Mosciano Sant'Angelo - Diodoro Ecologia",
    "Enna - Eco Enna Servizi",
    "Assisi - ECE Srl",
    "Cancello ed Arnone - WM Magenta Srl",
    "Isontina Ambiente",
    "Minturno",
    "Oristano - Formula Ambiente Spa",
    "Junker",
    "Alife - CZETA Spa",
    "Castel Gandolfo - Coop 134",
    "Comuni della Convenzione di Sesto Calende - Econord",
    "Gallo Matese",
    "Castelvetrano",
    "Arosio - Service 24 Ambiente Srl",
    "Sardegna Ecology - Ciclat",
    "Cosvega",
    "Perdasdefogu - Eco-Sistemi",
    "Curti - WM Magenta Srl",
    "Fiuggi",
    "Ussita",
    "Santa Maria a Vico",
    "Artena",
    "Triora",
    "Comunità delle Giudicarie",
    "Monte Urano - Eco Elpidiense Srl",
    "Iglesias",
    "Frosinone - De Vizia Transfer Spa",
    "GEA Srl",
    "Cidiu",
    "Sermoneta - Del Prete Srl",
    "Montecassiano",
    "Vieste - Impregico Srl",
    "Passerano Marmorito",
    "CISA",
    "Camerino",
    "Minerva Ambiente",
    "Unione Castello di Gerione - Giuliani Environment",
    "Assago - San Germano - Gruppo Iren",
    "Amaie Energia e Servizi Srl",
    "Rho - A.Se.R SpA",
    "Castel Volturno - WM Magenta Srl",
    "Stefanaconi",
    "Pietrabruna",
    "Brixen/Bressanone - Stadtwerke Brixen AG/ASM Bressanone SpA",
    "Piazza Brembana",
    "Guardistallo",
    "Ripalimosani",
    "ATO2 - Ancona",
    "Silvi - Diodoro Ecologia",
    "Sesto San Giovanni - Impresa Sangalli",
    "Turate - Turcato Snc",
    "Ossago Lodigiano",
    "Isole Tremiti - Smaltimenti Sud",
    "Asm Terni",
    "Leporano - Impregico Srl",
    "Avellino - Grande Srl",
    "Vitorchiano",
    "Castelsardo",
    "Lentate sul Seveso",
    "EcoInnova Srl",
    "Zambrone - Tecnew Srl",
    "Squillace - Sieco Spa",
    "Unione Comuni Alta Marmilla - Formula Ambiente Spa",
    "Carpignano Salentino",
    "Faleria",
    "Mentana - Paoletti Ecologia",
    "Marche Multiservizi Falconara",
    "Villanterio",
    "ASIA Azienda Speciale per l'Igiene Ambientale",
    "Valle Camonica Servizi Srl",
    "Cooperativa Trasforma",
    "Patti - Pizzo Pippo",
    "Noventa di Piave",
    "Palata",
    "Monte di Procida - DM Technology Srl",
    "Tricase",
    "Merano - ASM",
    "Consac",
    "Unione Terra dei Castelli",
    "Sasom",
    "Roccella Ionica - Jonica Multiservizi Spa",
    "Suno",
    "Terno d'Isola",
    "Saponara",
    "Altavilla Irpina",
    "Monza - Impresa Sangalli",
    "Brembate",
    "Chiusavecchia",
    "ARO Figulinas - DLR Ambiente - Ciclat",
    "Soleto",
    "Gioiosa Marea - Pizzo Pippo",
    "Amag Ambiente",
    "Consorzio Area Vasta Basso Novarese",
    "Cosp Tecno Service",
    "Osimo - Astea",
    "A&T 2000 Spa",
    "Vicoforte",
    "Rieco - Abruzzo",
    "Bacino Ventimigliese - TeknoService",
    "Villaputzu",
    "Collinas",
    "Budoni - Formula Ambiente Spa",
    "Santi Cosma e Damiano",
    "Comunità della Vallagarina - Dolomiti Ambiente Srl",
    "Cabras",
    "Garfagnana Ecologia Ambiente - GEA",
    "Traona",
    "Mondragone - DHI",
    "Asti - ASP S.p.A.",
    "Belforte del Chienti",
    "AnconAmbiente",
    "Sennori e Sorso - Gesenu Spa",
    "Volterra",
    "Ardea - DM Technology Srl",
    "Salerno - Salerno Pulita Spa",
    "Orosei - Sceas - Ciclat",
    "Montelongo - Rotello - San Giuliano di Puglia - Impregico Srl",
    "Amalfi",
    "Lodè - Eco Flap - Ciclat",
    "Toro",
    "C.C.S. - Consorzio Campale Stabile",
}


def EXTRA_INFO():
    for s in SERVICE_PROVIDERS:
        yield {"title": s, "country": "it"}


# MUNICIPALITIES That do return to be supported but do not offer a calendar
# Do not provide calendar
# Eco Burgus Srl
# Acea Pinerolese
# Egna
# Pontecorvo
# Sogliano Cavour - Teknowaste Srl
# Tarvisio


TEST_CASES = {
    "Unione dei Comuni di Valmalenco, Boroneddu": {"municipality": "Boroneddu"},
    "Mosciano Sant'Angelo": {"municipality": "Mosciano Sant'Angelo"},
    "Lodè": {"municipality": "Lodè", "area": "Utenze non domestiche"},
}


class Source(Junker):
    def __init__(self, municipality: str, area: str | None = None):
        super().__init__(municipality, area_name=area, use_embed_url=False)

    def fetch(self):
        try:
            return super().fetch()
        except AreaRequired as e:
            raise SourceArgumentRequiredWithSuggestions(
                "area", "required for this municipality", [a[0] for a in e.areas]
            )
        except AreaNotFound as e:
            raise SourceArgumentNotFoundWithSuggestions(
                "area", self._area, [a[0] for a in e.areas]
            )
