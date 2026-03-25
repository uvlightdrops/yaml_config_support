"""Kleine Hilfsklasse für optionale Konsolenausgabe."""

class OutputControl:
    """Stellt eine einfache, über ``verbose`` steuerbare Log-Ausgabe bereit."""

    def __init__(self, verbose=False):
        """Initialisiert die Ausgabesteuerung.

        Args:
            verbose: Wenn ``True``, werden Nachrichten über :meth:`out`
                auf ``stdout`` ausgegeben.
        """
        self.verbose = verbose

    def out(self, *args):
        """Gibt eine Log-Nachricht aus, wenn ``verbose`` aktiviert ist.

        Args:
            *args: Beliebige Textfragmente, die mit Leerzeichen verbunden
                ausgegeben werden.
        """
        if self.verbose:
            print('LOG ' + ' '.join(args))
