"""HackNotes — carnet de notes de pirate (Kivy, Android).

Application **100% autonome** (stdlib `sqlite3` + Kivy), comme NetScan : elle ne
réutilise aucun autre module du dépôt, donc rien n'est copié au build.

Les notes sont stockées dans une base SQLite locale, dans le dossier privé de
l'app (`App.user_data_dir`, accessible en écriture sur Android). Chaque note a un
titre, une catégorie (ex. « Lab », « Cible », « Technique », « Recon »), un
contenu, et des dates de création/màj.

UI : deux écrans (liste + éditeur) via le `ScreenManager` intégré de Kivy.
Conventions reprises de `monappli/`/`netscan/` : `_esc()` échappe le markup Kivy
avant tout affichage de texte dynamique en `markup=True`.

Test local : `pip install kivy`, puis `python hacknotes/main.py`.
"""

import os
import sqlite3
from datetime import datetime

from kivy.app import App
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import Screen, ScreenManager, SlideTransition
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput

# --- Couleurs par catégorie (module-level, comme SEVERITY_COLORS de monappli) ---
CATEGORY_COLORS = {
    "Lab": "00b894",        # vert
    "Cible": "e17055",      # orange (une cible à tester)
    "Technique": "0984e3",  # bleu (une commande / méthode)
    "Recon": "6c5ce7",      # violet
    "Faille": "d63031",     # rouge (une vuln trouvée)
}
DEFAULT_COLOR = "b2bec3"    # gris pour les catégories libres


def _esc(text):
    """Échappe les métacaractères du markup Kivy avant un affichage markup=True."""
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("[", "&bl;")
        .replace("]", "&br;")
    )


def _color_for(category):
    """Retourne le code couleur hexa associé à une catégorie (gris par défaut)."""
    return CATEGORY_COLORS.get((category or "").strip(), DEFAULT_COLOR)


# --------------------------------------------------------------------------- #
#                              Couche base de données                          #
# --------------------------------------------------------------------------- #
SCHEMA = """
CREATE TABLE IF NOT EXISTS notes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    title     TEXT NOT NULL,
    category  TEXT NOT NULL DEFAULT '',
    content   TEXT NOT NULL DEFAULT '',
    created   TEXT NOT NULL,
    updated   TEXT NOT NULL
);
"""


def connect(path):
    """Ouvre (et crée si besoin) la base SQLite des notes."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript(SCHEMA)
    conn.commit()
    return conn


def list_notes(conn, query=""):
    """Liste les notes (plus récentes d'abord), filtrées par titre/catégorie/contenu."""
    query = (query or "").strip()
    if query:
        like = f"%{query}%"
        rows = conn.execute(
            "SELECT * FROM notes "
            "WHERE title LIKE ? OR category LIKE ? OR content LIKE ? "
            "ORDER BY updated DESC",
            (like, like, like),
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM notes ORDER BY updated DESC").fetchall()
    return rows


def get_note(conn, note_id):
    return conn.execute("SELECT * FROM notes WHERE id = ?", (note_id,)).fetchone()


def add_note(conn, title, category, content):
    now = datetime.now().isoformat(timespec="seconds")
    cur = conn.execute(
        "INSERT INTO notes (title, category, content, created, updated) "
        "VALUES (?, ?, ?, ?, ?)",
        (title, category, content, now, now),
    )
    conn.commit()
    return cur.lastrowid


def update_note(conn, note_id, title, category, content):
    now = datetime.now().isoformat(timespec="seconds")
    conn.execute(
        "UPDATE notes SET title = ?, category = ?, content = ?, updated = ? "
        "WHERE id = ?",
        (title, category, content, now, note_id),
    )
    conn.commit()


def delete_note(conn, note_id):
    conn.execute("DELETE FROM notes WHERE id = ?", (note_id,))
    conn.commit()


# --------------------------------------------------------------------------- #
#                              Écran : liste des notes                         #
# --------------------------------------------------------------------------- #
class ListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        title = Label(
            text="[b]🏴‍☠️ HackNotes[/b]",
            markup=True,
            font_size="24sp",
            size_hint_y=None,
            height=dp(44),
        )
        root.add_widget(title)

        # Barre de recherche
        self.search = TextInput(
            hint_text="🔍 Rechercher (titre, catégorie, contenu)…",
            multiline=False,
            size_hint_y=None,
            height=dp(44),
        )
        self.search.bind(text=lambda *_: self.refresh())
        root.add_widget(self.search)

        # Liste défilante des notes
        self.scroll = ScrollView()
        self.notes_box = BoxLayout(
            orientation="vertical", size_hint_y=None, spacing=dp(6), padding=dp(2)
        )
        self.notes_box.bind(minimum_height=self.notes_box.setter("height"))
        self.scroll.add_widget(self.notes_box)
        root.add_widget(self.scroll)

        # Bouton nouvelle note
        new_btn = Button(
            text="➕ Nouvelle note",
            size_hint_y=None,
            height=dp(52),
            background_color=(0, 0.72, 0.58, 1),
        )
        new_btn.bind(on_release=self.new_note)
        root.add_widget(new_btn)

        self.add_widget(root)

    def on_pre_enter(self, *args):
        self.refresh()

    def refresh(self):
        self.notes_box.clear_widgets()
        app = App.get_running_app()
        rows = list_notes(app.conn, self.search.text)

        if not rows:
            self.notes_box.add_widget(
                Label(
                    text="Aucune note. Appuie sur « ➕ Nouvelle note ».",
                    size_hint_y=None,
                    height=dp(40),
                )
            )
            return

        for row in rows:
            self.notes_box.add_widget(self._note_card(row))

    def _note_card(self, row):
        color = _color_for(row["category"])
        cat = row["category"] or "—"
        date = row["updated"].replace("T", " ")
        text = (
            f"[b]{_esc(row['title'])}[/b]\n"
            f"[color=#{color}]● {_esc(cat)}[/color]  "
            f"[size=11sp][color=#888888]{_esc(date)}[/color][/size]"
        )
        btn = Button(
            text=text,
            markup=True,
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(64),
            background_color=(0.16, 0.18, 0.22, 1),
        )
        btn.bind(size=lambda b, *_: setattr(b, "text_size", (b.width - dp(20), None)))
        btn.bind(on_release=lambda b, nid=row["id"]: self.open_note(nid))
        return btn

    def new_note(self, *_):
        editor = self.manager.get_screen("editor")
        editor.load(None)
        self.manager.transition.direction = "left"
        self.manager.current = "editor"

    def open_note(self, note_id):
        editor = self.manager.get_screen("editor")
        editor.load(note_id)
        self.manager.transition.direction = "left"
        self.manager.current = "editor"


# --------------------------------------------------------------------------- #
#                              Écran : éditeur                                 #
# --------------------------------------------------------------------------- #
class EditorScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.note_id = None

        root = BoxLayout(orientation="vertical", padding=dp(8), spacing=dp(8))

        self.title_input = TextInput(
            hint_text="Titre de la note",
            multiline=False,
            size_hint_y=None,
            height=dp(44),
        )
        root.add_widget(self.title_input)

        self.category_input = TextInput(
            hint_text="Catégorie (Lab, Cible, Technique, Recon, Faille…)",
            multiline=False,
            size_hint_y=None,
            height=dp(44),
        )
        root.add_widget(self.category_input)

        self.content_input = TextInput(
            hint_text="Contenu : commandes, URLs, étapes, observations…",
        )
        root.add_widget(self.content_input)

        # Barre d'actions
        actions = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(8))

        back_btn = Button(text="⬅ Retour", background_color=(0.4, 0.4, 0.45, 1))
        back_btn.bind(on_release=self.go_back)
        actions.add_widget(back_btn)

        self.delete_btn = Button(text="🗑 Suppr.", background_color=(0.84, 0.19, 0.19, 1))
        self.delete_btn.bind(on_release=self.confirm_delete)
        actions.add_widget(self.delete_btn)

        save_btn = Button(text="💾 Enregistrer", background_color=(0, 0.52, 0.89, 1))
        save_btn.bind(on_release=self.save)
        actions.add_widget(save_btn)

        root.add_widget(actions)
        self.add_widget(root)

    def load(self, note_id):
        """Charge une note existante, ou prépare une note vierge si note_id None."""
        self.note_id = note_id
        if note_id is None:
            self.title_input.text = ""
            self.category_input.text = ""
            self.content_input.text = ""
            self.delete_btn.disabled = True
        else:
            app = App.get_running_app()
            row = get_note(app.conn, note_id)
            if row is None:  # supprimée entre-temps
                self.note_id = None
                return
            self.title_input.text = row["title"]
            self.category_input.text = row["category"]
            self.content_input.text = row["content"]
            self.delete_btn.disabled = False

    def save(self, *_):
        title = self.title_input.text.strip()
        if not title:
            self._popup("Titre manquant", "Donne au moins un titre à ta note.")
            return
        category = self.category_input.text.strip()
        content = self.content_input.text
        app = App.get_running_app()
        if self.note_id is None:
            add_note(app.conn, title, category, content)
        else:
            update_note(app.conn, self.note_id, title, category, content)
        self.go_back()

    def confirm_delete(self, *_):
        if self.note_id is None:
            return
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(10))
        box.add_widget(Label(text="Supprimer cette note ?"))
        btns = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(8))
        popup = Popup(title="Confirmation", content=box, size_hint=(0.8, 0.4))

        cancel = Button(text="Annuler")
        cancel.bind(on_release=popup.dismiss)
        btns.add_widget(cancel)

        confirm = Button(text="Supprimer", background_color=(0.84, 0.19, 0.19, 1))

        def _do(*_a):
            app = App.get_running_app()
            delete_note(app.conn, self.note_id)
            popup.dismiss()
            self.go_back()

        confirm.bind(on_release=_do)
        btns.add_widget(confirm)
        box.add_widget(btns)
        popup.open()

    def _popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4),
        )
        popup.open()
        Clock.schedule_once(lambda *_: popup.dismiss(), 2)

    def go_back(self, *_):
        self.manager.transition.direction = "right"
        self.manager.current = "list"


# --------------------------------------------------------------------------- #
#                                   App                                        #
# --------------------------------------------------------------------------- #
class HackNotesApp(App):
    def build(self):
        self.title = "HackNotes"
        db_path = os.path.join(self.user_data_dir, "hacknotes.db")
        self.conn = connect(db_path)

        sm = ScreenManager(transition=SlideTransition())
        sm.add_widget(ListScreen(name="list"))
        sm.add_widget(EditorScreen(name="editor"))
        return sm

    def on_stop(self):
        try:
            self.conn.close()
        except Exception:
            pass


if __name__ == "__main__":
    HackNotesApp().run()
