from idlelib.run import StdOutputFile

from database.regione_DAO import RegioneDAO
from database.tour_DAO import TourDAO
from database.attrazione_DAO import AttrazioneDAO

class Model:
    def __init__(self):
        self.tour_map = {} # Mappa ID tour -> oggetti Tour
        self.attrazioni_map = {} # Mappa ID attrazione -> oggetti Attrazione

        self._pacchetto_ottimo = []
        self._valore_ottimo: int = -1
        self._costo = 0
        self._tour_candidati = [] #lista dove inserisco solo i tour che servono in base alla regione selezionata



        # Caricamento
        self.load_tour()
        self.load_attrazioni()
        self.load_relazioni()

    @staticmethod
    def load_regioni():
        """ Restituisce tutte le regioni disponibili """
        return RegioneDAO.get_regioni()

    def load_tour(self):
        """ Carica tutti i tour in un dizionario [id, Tour]"""
        self.tour_map = TourDAO.get_tour()

    def load_attrazioni(self):
        """ Carica tutte le attrazioni in un dizionario [id, Attrazione]"""
        self.attrazioni_map = AttrazioneDAO.get_attrazioni()

    def load_relazioni(self):
        """
            Interroga il database per ottenere tutte le relazioni fra tour e attrazioni e salvarle nelle strutture dati
            Collega tour <-> attrazioni.
            --> Ogni Tour ha un set di Attrazione.
            --> Ogni Attrazione ha un set di Tour.
        """
        lista_relazione = TourDAO.get_tour_attrazioni() # relazione N:N [id_tour | id_attrazione ]

        for rel in lista_relazione:
            self.tour_map[rel['id_tour']].attrazioni.add(rel['id_attrazione'])
            self.attrazioni_map[rel['id_attrazione']].tour.add(rel['id_tour'])






    def genera_pacchetto(self, id_regione: str, max_giorni: int = None, max_budget: float = None):
        """
        Calcola il pacchetto turistico ottimale per una regione rispettando i vincoli di durata, budget e attrazioni uniche.
        :param id_regione: id della regione
        :param max_giorni: numero massimo di giorni (può essere None --> nessun limite)
        :param max_budget: costo massimo del pacchetto (può essere None --> nessun limite)

        :return: self._pacchetto_ottimo (una lista di oggetti Tour)
        :return: self._costo (il costo del pacchetto)
        :return: self._valore_ottimo (il valore culturale del pacchetto)
        """
        self._pacchetto_ottimo = []
        self._costo = 0
        self._valore_ottimo = -1
        self._tour_candidati = []

        for t in self.tour_map.values(): #for per prendere solamente i tour della regione scelta(minimizzare le operazioni che il calcolaatore deve eseguire)
            if t.id_regione == id_regione:
                self._tour_candidati.append(t)
        self._ricorsione(0,[],0,0,0,set(),max_giorni, max_budget) #chiamo la ricorsione



        return self._pacchetto_ottimo, self._costo, self._valore_ottimo

    def _ricorsione(self, start_index: int, pacchetto_parziale: list, durata_corrente: int,
                    costo_corrente: float, valore_corrente: int, attrazioni_usate: set,
                    max_giorni: int, max_budget: float):

        # verifica se la soluzione attuale è migliore del massimo trovato finora
        if valore_corrente > self._valore_ottimo:
            self._valore_ottimo = valore_corrente
            self._pacchetto_ottimo = pacchetto_parziale.copy()  # faccio una copia della lista per salvarla
            self._costo = costo_corrente

        # caso base: interrompo se ho esaminato tutti i tour disponibili
        if start_index >= len(self._tour_candidati):
            return

        # recupero il tour corrente dalla lista filtrata
        tour_corrente = self._tour_candidati[start_index]

        # ramo 1: provo ad aggiungere il tour (take)

        # verifica vincolo budget
        budget_ok = True
        if max_budget is not None and (costo_corrente + tour_corrente.costo) > max_budget:
            budget_ok = False

        # verifica vincolo durata
        durata_ok = True
        if max_giorni is not None and (durata_corrente + tour_corrente.durata_giorni) > max_giorni:
            durata_ok = False

        # verifica vincolo attrazioni duplicate (isdisjoint ritorna true se non ci sono elementi comuni)
        attrazioni_ok = attrazioni_usate.isdisjoint(tour_corrente.attrazioni)

        # se tutti i vincoli sono rispettati, procedo con l'aggiunta
        if budget_ok and durata_ok and attrazioni_ok:

            # calcolo il valore culturale sommando quello delle singole attrazioni
            valore_tour_curr = 0
            for id_attr in tour_corrente.attrazioni:
                valore_tour_curr += self.attrazioni_map[id_attr].valore_culturale

            # aggiungo il tour e le sue attrazioni alle strutture dati parziali
            pacchetto_parziale.append(tour_corrente)
            for att in tour_corrente.attrazioni:
                attrazioni_usate.add(att)

            # chiamata ricorsiva aggiornando i contatori (costo, durata, valore)
            self._ricorsione(
                start_index + 1,
                pacchetto_parziale,
                durata_corrente + tour_corrente.durata_giorni,
                costo_corrente + tour_corrente.costo,
                valore_corrente + valore_tour_curr,
                attrazioni_usate,
                max_giorni, max_budget
            )

            # backtracking: rimuovo l'ultimo tour e le sue attrazioni per ripristinare lo stato
            pacchetto_parziale.pop()
            for att in tour_corrente.attrazioni:
                attrazioni_usate.remove(att)

        # ramo 2: salto il tour corrente e passo al successivo
        self._ricorsione(
            start_index + 1,
            pacchetto_parziale,
            durata_corrente,
            costo_corrente,
            valore_corrente,
            attrazioni_usate,
            max_giorni, max_budget
        )
