"""Gerarchia delle eccezioni personalizzate dell'applicazione.

Fornisce eccezioni specifiche per dominio che permettono una
gestione degli errori granulare e una presentazione all'utente
informativa e contestualizzata.
"""

from __future__ import annotations


class AppError(Exception):
    """Classe base per tutte le eccezioni dell'applicazione.

    Attributes:
        message: Messaggio descrittivo dell'errore.
        details: Dettagli aggiuntivi opzionali.
    """

    def __init__(self, message: str, details: str = "") -> None:
        """Inizializza l'eccezione con messaggio e dettagli.

        Args:
            message: Messaggio descrittivo dell'errore.
            details: Dettagli aggiuntivi opzionali.
        """
        super().__init__(message)
        self.message = message
        self.details = details


class ScraperError(AppError):
    """Errore durante lo scraping dei dati dal sito web."""

    pass


class ScraperConnectionError(ScraperError):
    """Errore di connessione al sito web."""

    pass


class ScraperParseError(ScraperError):
    """Errore durante il parsing del contenuto HTML."""

    pass


class ConfigError(AppError):
    """Errore nella configurazione dell'applicazione."""

    pass


class ConfigValidationError(ConfigError):
    """Errore di validazione di un valore di configurazione."""

    pass
