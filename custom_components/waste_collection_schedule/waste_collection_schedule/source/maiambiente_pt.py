import datetime

from waste_collection_schedule import Collection, Icons  # type: ignore[attr-defined]
from waste_collection_schedule.exceptions import SourceArgumentNotFoundWithSuggestions
from waste_collection_schedule.service.Maiambiente import (
    LABELS,
    Cliente,
    MaiambienteError,
    ler_calendario,
)

TITLE = "Maiambiente"
DESCRIPTION = "Source for waste collection schedules in Maia, Portugal."
URL = "https://www.maiambiente.pt"
COUNTRY = "pt"

SOURCE_CODEOWNERS = ["@CargoTechSolutions"]

# Public buildings, deliberately: these run on every scheduled source test.
TEST_CASES = {
    "Câmara Municipal da Maia": {
        "rua": "Praca Doutor Jose Vieira Carvalho (Cidade Da Maia (Maia))",
        "numero": "Edificio dos Paços do Conselho",
    },
    "Biblioteca da Maia": {
        "rua": "Rua Engenheiro Duarte Pacheco (Cidade Da Maia (Maia))",
        "numero": "Biblioteca da Maia",
    },
}

ICON_MAP = {
    "Vidro": Icons.GLASS,
    "Embalagens de plástico e metal": Icons.PLASTIC_PACKAGING,
    "Papel e cartão": Icons.PAPER,
    "Resíduos alimentares": Icons.BIO_KITCHEN,
    "Resíduos de jardim": Icons.GARDEN,
    "Resíduos indiferenciados": Icons.GENERAL_WASTE,
    "Não haverá recolha": Icons.NO_COLLECTION,
}

HOW_TO_GET_ARGUMENTS_DESCRIPTION = {
    "en": (
        "Search for your street at https://servicos.maiambiente.pt/cal2026/ and "
        "use the exact street name from the suggestion list; it includes the "
        "parish in brackets, for example `Rua Engenheiro Duarte Pacheco "
        "(Cidade Da Maia (Maia))`. Then use your house number exactly as "
        "listed; some are compound (`76, 1`, `118, Rc`) and "
        "some are building names. Note the site's search ignores Portuguese "
        "prepositions: search for `Vieira Carvalho`, not `Vieira de Carvalho`."
    ),
}

PARAM_DESCRIPTIONS = {
    "en": {
        "rua": "Exact street name as listed by Maiambiente, parish included.",
        "numero": "House number exactly as listed for that street.",
    },
}

PARAM_TRANSLATIONS = {
    "en": {
        "rua": "Street",
        "numero": "House number",
    },
}

# How close to the end of the current calendar we start looking for the next
# year's one. Maiambiente publishes it during December.
MARGEM_FIM = 45


class Source:
    """Maiambiente's yearly collection calendar, without login and without OCR.

    The public lookup resolves street -> house number -> collection circuit ->
    yearly PDF. The body of that PDF is a bitmap holding a regular grid of
    coloured circles: the date comes from the geometry (block = month, row =
    weekday, column = week) and the waste stream comes from the fill colour.
    The numbers printed inside the circles are never read.

    Everything Maiambiente serves carries the year in its path
    (`cal2026/cal2026.php`, `type=arruamento2026`, ...), so the year is always
    a parameter and the address is re-resolved per year - one year's `idcal` is
    not necessarily valid in the next.

    The calendar belongs to the CIRCUIT rather than to the address and covers a
    whole year, so each year is fetched once per instance and kept in memory.
    """

    def __init__(self, rua: str, numero: str):
        self._rua = rua
        self._numero = str(numero)
        self._cache: dict[int, dict] = {}

    def _calendario(self, ano: int) -> dict:
        if ano in self._cache:
            return self._cache[ano]

        cli = Cliente(ano)
        numeros = cli.numeros(self._rua)
        if not numeros:
            raise SourceArgumentNotFoundWithSuggestions(
                "rua", self._rua, cli.arruamentos(self._rua.split("(")[0].strip())
            )

        alvo = next((n for n in numeros if n["numero"] == self._numero), None)
        if alvo is None:
            # some numbers are compound ("76, 1"); accept the leading part too
            alvo = next(
                (
                    n
                    for n in numeros
                    if n["numero"].split(",")[0].strip() == self._numero
                ),
                None,
            )
        if alvo is None:
            raise SourceArgumentNotFoundWithSuggestions(
                "numero", self._numero, [n["numero"] for n in numeros]
            )

        pdf = cli.pdf(alvo["idcal"], alvo["idunico"], self._rua, alvo["numero"])
        eventos, _ = ler_calendario(pdf, ano)
        self._cache[ano] = eventos
        return eventos

    def fetch(self) -> list[Collection]:
        hoje = datetime.date.today()
        eventos: dict[datetime.date, list[str]] = dict(self._calendario(hoje.year))

        # The calendar runs into the first days of January, so once the end is
        # in sight we look for next year's. Only a MaiambienteError is tolerated
        # here, and only for the *next* year: it means Maiambiente has not
        # published that calendar yet, which is normal for most of the year.
        # Any failure of the current year's calendar propagates untouched.
        if eventos and (max(eventos) - hoje).days < MARGEM_FIM:
            try:
                eventos.update(self._calendario(hoje.year + 1))
            except MaiambienteError:
                pass

        return [
            Collection(date=dia, t=LABELS[fluxo], icon=ICON_MAP.get(LABELS[fluxo]))
            for dia, fluxos in sorted(eventos.items())
            for fluxo in fluxos
        ]
