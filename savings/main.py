#!/usr/bin/env python3
"""Suivi Épargne — objectif 1 000 000 €"""

import sqlite3
import os
from datetime import datetime

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.spinner import Spinner
from kivy.uix.progressbar import ProgressBar
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle

GOAL = 1_000_000.0

MONTH_NAMES_FR = [
    "", "Janvier", "Février", "Mars", "Avril", "Mai", "Juin",
    "Juillet", "Août", "Septembre", "Octobre", "Novembre", "Décembre",
]

VEHICLE_COLORS = [
    "#1976D2", "#7B1FA2", "#E64A19",
    "#388E3C", "#F57C00", "#0097A7", "#C62828",
]


def _esc(text):
    return str(text).replace("&", "&amp;").replace("[", "&#91;").replace("]", "&#93;")


def fmt_money(amount):
    """1 234 567.89 €"""
    parts = f"{abs(amount):,.2f}".split(".")
    integer_part = parts[0].replace(",", " ")
    sign = "-" if amount < 0 else ""
    return f"{sign}{integer_part},{parts[1]} €"


def future_value(principal, monthly, annual_rate_pct, months):
    """Valeur future avec intérêts composés mensuels + versements mensuels."""
    if annual_rate_pct <= 0:
        return principal + monthly * months
    i = annual_rate_pct / 100.0 / 12.0
    growth = (1 + i) ** months
    return principal * growth + monthly * ((growth - 1) / i)


def months_to_goal(principal, monthly, annual_rate_pct, goal):
    """Nombre de mois pour atteindre l'objectif (intérêts composés)."""
    if principal >= goal:
        return 0
    if annual_rate_pct <= 0:
        return (goal - principal) / monthly if monthly > 0 else float("inf")
    i = annual_rate_pct / 100.0 / 12.0
    base = principal + monthly / i
    if base <= 0:
        return float("inf")
    target = (goal + monthly / i) / base
    if target <= 1:
        return float("inf")
    import math
    return math.log(target) / math.log(1 + i)


def hex_to_rgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i+2], 16) / 255.0 for i in (0, 2, 4))


def db_connect():
    try:
        path = os.path.join(App.get_running_app().user_data_dir, "savings.db")
    except Exception:
        path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savings.db")
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.executescript("""
        PRAGMA foreign_keys = ON;
        CREATE TABLE IF NOT EXISTS vehicles (
            id             INTEGER PRIMARY KEY AUTOINCREMENT,
            name           TEXT    NOT NULL UNIQUE,
            monthly_amount REAL    NOT NULL DEFAULT 0,
            current_total  REAL    NOT NULL DEFAULT 0,
            color_idx      INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS entries (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            vehicle_id INTEGER REFERENCES vehicles(id) ON DELETE CASCADE,
            year       INTEGER NOT NULL,
            month      INTEGER NOT NULL,
            amount     REAL    NOT NULL,
            note       TEXT,
            created_at TEXT    DEFAULT (datetime('now'))
        );
    """)
    if not conn.execute("SELECT 1 FROM vehicles LIMIT 1").fetchone():
        conn.executemany(
            "INSERT OR IGNORE INTO vehicles (name, monthly_amount, current_total, color_idx)"
            " VALUES (?,?,?,?)",
            [
                ("Assurance Vie", 743.63, 0.0, 0),
                ("PER",            30.0,  0.0, 1),
                ("PEL",            50.0,  0.0, 2),
            ],
        )
        conn.commit()
    return conn


# ── UI helpers ────────────────────────────────────────────────────────────────

def bg_card(widget, r, g, b, a=1.0):
    """Paint a solid background on widget; returns the Rectangle for later binding."""
    with widget.canvas.before:
        Color(r, g, b, a)
        rect = Rectangle(pos=widget.pos, size=widget.size)
    widget.bind(
        pos=lambda w, v, rr=rect: setattr(rr, "pos", v),
        size=lambda w, v, rr=rect: setattr(rr, "size", v),
    )
    return rect


def card(color_hex="#1E2A4A", height=None, padding=12, spacing=6, orientation="vertical"):
    c = BoxLayout(
        orientation=orientation,
        size_hint_y=None,
        height=dp(height) if height else dp(80),
        padding=dp(padding),
        spacing=dp(spacing),
    )
    r, g, b = hex_to_rgb(color_hex)
    bg_card(c, r, g, b)
    return c


# ── App ───────────────────────────────────────────────────────────────────────

class SavingsApp(App):

    def build(self):
        self.conn = db_connect()
        self.current_tab = "dashboard"
        self.rate_pct = 3  # rendement annuel par défaut (%)

        root = BoxLayout(orientation="vertical", spacing=0)
        bg_card(root, 0.07, 0.08, 0.13)

        root.add_widget(self._build_header())
        root.add_widget(self._build_tabs())

        self.content_area = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
            padding=dp(10),
        )
        self.content_area.bind(minimum_height=self.content_area.setter("height"))

        scroll = ScrollView()
        scroll.add_widget(self.content_area)
        root.add_widget(scroll)

        self.refresh()
        return root

    # ── Header ────────────────────────────────────────────────────────────────

    def _build_header(self):
        hdr = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(110),
            padding=dp(10),
            spacing=dp(4),
        )
        bg_card(hdr, 0.08, 0.12, 0.25)

        self.title_lbl = Label(
            text="[b]💰 Objectif Épargne — 1 000 000 €[/b]",
            markup=True, font_size=dp(18),
            size_hint_y=None, height=dp(32),
            color=(1, 0.85, 0.2, 1),
        )
        hdr.add_widget(self.title_lbl)

        self.progress_lbl = Label(
            text="Chargement…",
            markup=True, font_size=dp(12),
            size_hint_y=None, height=dp(22),
            color=(0.85, 0.85, 0.85, 1),
        )
        hdr.add_widget(self.progress_lbl)

        self.progress_bar = ProgressBar(
            max=100, value=0,
            size_hint_y=None, height=dp(18),
        )
        hdr.add_widget(self.progress_bar)

        self.eta_lbl = Label(
            text="",
            markup=True, font_size=dp(11),
            size_hint_y=None, height=dp(18),
            color=(0.6, 0.85, 1.0, 1),
        )
        hdr.add_widget(self.eta_lbl)
        return hdr

    # ── Tab bar ───────────────────────────────────────────────────────────────

    def _build_tabs(self):
        tabs = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(2), padding=(dp(2), dp(2)))
        bg_card(tabs, 0.1, 0.13, 0.22)

        self._tab_btns = {}
        tab_defs = [
            ("dashboard", "📊 Bilan"),
            ("vehicles",  "🏦 Comptes"),
            ("entry",     "➕ Saisir"),
            ("history",   "📋 Histo"),
        ]
        for tid, tlabel in tab_defs:
            btn = Button(
                text=tlabel, font_size=dp(12),
                background_normal="",
                background_color=(0.2, 0.35, 0.65, 1),
                color=(1, 1, 1, 1),
            )
            btn.bind(on_press=lambda b, t=tid: self.switch_tab(t))
            tabs.add_widget(btn)
            self._tab_btns[tid] = btn

        self._highlight_tab("dashboard")
        return tabs

    def _highlight_tab(self, active):
        for tid, btn in self._tab_btns.items():
            btn.background_color = (0.25, 0.45, 0.85, 1) if tid == active else (0.12, 0.18, 0.32, 1)

    def switch_tab(self, tab_id):
        self.current_tab = tab_id
        self._highlight_tab(tab_id)
        self.refresh()

    # ── Data helpers ──────────────────────────────────────────────────────────

    def get_stats(self):
        rows = self.conn.execute("SELECT * FROM vehicles ORDER BY id").fetchall()
        total   = sum(r["current_total"]  for r in rows)
        monthly = sum(r["monthly_amount"] for r in rows)
        pct     = min(total / GOAL * 100, 100) if GOAL else 0
        months_left = months_to_goal(total, monthly, self.rate_pct, GOAL)
        return rows, total, monthly, pct, months_left

    def refresh(self):
        rows, total, monthly, pct, months_left = self.get_stats()

        # Header
        self.progress_lbl.text = (
            f"[b]{_esc(fmt_money(total))}[/b] / {_esc(fmt_money(GOAL))}"
            f"  •  [b]{pct:.2f}%[/b]  •  {_esc(fmt_money(monthly))}/mois"
        )
        self.progress_bar.value = pct

        if total >= GOAL:
            self.eta_lbl.text = "🎉 Félicitations — objectif atteint !"
        elif months_left == float("inf"):
            self.eta_lbl.text = "⏱ Configurez vos versements mensuels pour voir l'ETA"
        else:
            yrs = months_left / 12
            if yrs >= 2:
                self.eta_lbl.text = f"⏱ ~{yrs:.1f} ans ({int(months_left)} mois) à {self.rate_pct}% de rendement"
            else:
                self.eta_lbl.text = f"⏱ ~{int(months_left)} mois à {self.rate_pct}% de rendement"

        # Content
        self.content_area.clear_widgets()
        if self.current_tab == "dashboard":
            self._tab_dashboard(rows, total, monthly, pct, months_left)
        elif self.current_tab == "vehicles":
            self._tab_vehicles(rows)
        elif self.current_tab == "entry":
            self._tab_entry(rows)
        elif self.current_tab == "history":
            self._tab_history()

    # ── Dashboard tab ─────────────────────────────────────────────────────────

    def _tab_dashboard(self, rows, total, monthly, pct, months_left):
        # Big total card
        big = card("#0A1628", height=160, padding=14, spacing=6)
        big.add_widget(Label(
            text=f"[b][size=30]{_esc(fmt_money(total))}[/size][/b]",
            markup=True, color=(1, 0.85, 0.2, 1),
            size_hint_y=None, height=dp(50),
        ))
        big.add_widget(Label(
            text=f"sur [b]{_esc(fmt_money(GOAL))}[/b] — [b]{pct:.2f}%[/b]",
            markup=True, color=(0.75, 0.75, 0.75, 1),
            size_hint_y=None, height=dp(24), font_size=dp(13),
        ))
        pb = ProgressBar(max=100, value=pct, size_hint_y=None, height=dp(20))
        big.add_widget(pb)

        reste = GOAL - total
        big.add_widget(Label(
            text=f"Reste à épargner : [b][color=#FF8A65]{_esc(fmt_money(max(reste,0)))}[/color][/b]",
            markup=True, color=(0.8, 0.8, 0.8, 1),
            size_hint_y=None, height=dp(24), font_size=dp(12),
        ))
        self.content_area.add_widget(big)

        # Monthly recap
        mc = card("#0F2015", height=50, padding=12, spacing=4)
        mc.add_widget(Label(
            text=f"💳  Versements mensuels totaux : [b][color=#81C784]{_esc(fmt_money(monthly))}[/color][/b] / mois",
            markup=True, color=(0.85, 0.85, 0.85, 1), font_size=dp(13),
        ))
        self.content_area.add_widget(mc)

        # Per-vehicle cards
        self.content_area.add_widget(Label(
            text="[b]Répartition par compte[/b]",
            markup=True, color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=dp(30), font_size=dp(14),
        ))

        for row in rows:
            cr, cg, cb = hex_to_rgb(VEHICLE_COLORS[row["color_idx"] % len(VEHICLE_COLORS)])
            vc = BoxLayout(
                orientation="horizontal",
                size_hint_y=None, height=dp(72),
                padding=dp(10), spacing=dp(8),
            )
            bg_card(vc, cr * 0.18, cg * 0.18, cb * 0.18)

            # Accent bar
            acc = BoxLayout(size_hint_x=None, width=dp(6))
            bg_card(acc, cr, cg, cb)
            vc.add_widget(acc)

            info = BoxLayout(orientation="vertical", spacing=dp(2))
            pct_v = row["current_total"] / GOAL * 100 if GOAL else 0
            monthly_v = row["monthly_amount"]
            info.add_widget(Label(
                text=f"[b]{_esc(row['name'])}[/b]",
                markup=True, color=(1, 1, 1, 1), halign="left",
                text_size=(None, None), size_hint_y=0.45, font_size=dp(14),
            ))
            info.add_widget(Label(
                text=(
                    f"[b][color=#{int(cr*255):02x}{int(cg*255):02x}{int(cb*255):02x}]"
                    f"{_esc(fmt_money(row['current_total']))}[/color][/b]"
                    f"  ({pct_v:.3f}% de l'objectif)"
                ),
                markup=True, color=(0.85, 0.85, 0.85, 1), halign="left",
                text_size=(None, None), size_hint_y=0.3, font_size=dp(12),
            ))
            info.add_widget(Label(
                text=f"Versement : {_esc(fmt_money(monthly_v))} / mois",
                markup=True, color=(0.65, 0.65, 0.65, 1), halign="left",
                text_size=(None, None), size_hint_y=0.25, font_size=dp(11),
            ))
            vc.add_widget(info)
            self.content_area.add_widget(vc)

        # Projection table
        self.content_area.add_widget(Label(
            text="[b]Projections (intérêts composés)[/b]",
            markup=True, color=(0.7, 0.7, 0.7, 1),
            size_hint_y=None, height=dp(30), font_size=dp(14),
        ))

        # Sélecteur de rendement annuel (1 → 30 %)
        rate_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6),
                             padding=(dp(4), 0))
        rate_row.add_widget(Label(
            text="Rendement annuel :", color=(0.75, 0.75, 0.75, 1),
            halign="left", text_size=(None, None),
            size_hint_x=0.5, font_size=dp(13),
        ))
        rate_spinner = Spinner(
            text=f"{self.rate_pct} %",
            values=[f"{p} %" for p in range(1, 31)],
            size_hint_x=0.5,
            background_normal="", background_color=(0.18, 0.28, 0.5, 1),
            font_size=dp(14), color=(1, 1, 1, 1),
        )
        rate_spinner.bind(text=self._on_rate_change)
        rate_row.add_widget(rate_spinner)
        self.content_area.add_widget(rate_row)

        for label, months in [("1 an", 12), ("5 ans", 60), ("10 ans", 120), ("20 ans", 240)]:
            projected = future_value(total, monthly, self.rate_pct, months)
            gains = projected - (total + monthly * months)
            pc = card("#111827", height=52, padding=10, spacing=4, orientation="horizontal")
            left = BoxLayout(orientation="vertical", size_hint_x=0.4)
            left.add_widget(Label(
                text=f"Dans {label}", color=(0.8, 0.8, 0.8, 1),
                halign="left", text_size=(None, None), font_size=dp(13),
            ))
            left.add_widget(Label(
                text=f"[color=#777777]dont +{_esc(fmt_money(gains))} d'intérêts[/color]",
                markup=True, halign="left", text_size=(None, None), font_size=dp(10),
            ))
            pc.add_widget(left)
            color = "#81C784" if projected >= GOAL else "#FFB74D"
            pc.add_widget(Label(
                text=f"[b][color={color}]{_esc(fmt_money(projected))}[/color][/b]"
                     + (" 🏆" if projected >= GOAL else ""),
                markup=True, halign="right",
                text_size=(None, None), size_hint_x=0.6, font_size=dp(13),
            ))
            self.content_area.add_widget(pc)

    def _on_rate_change(self, spinner, text):
        try:
            self.rate_pct = int(text.replace("%", "").strip())
        except ValueError:
            self.rate_pct = 0
        self.refresh()

    # ── Vehicles tab ──────────────────────────────────────────────────────────

    def _tab_vehicles(self, rows):
        self.content_area.add_widget(Label(
            text="[b]🏦 Mes comptes épargne[/b]",
            markup=True, color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None, height=dp(34), font_size=dp(16),
        ))

        for row in rows:
            cr, cg, cb = hex_to_rgb(VEHICLE_COLORS[row["color_idx"] % len(VEHICLE_COLORS)])
            vc = BoxLayout(
                orientation="vertical",
                size_hint_y=None, height=dp(178),
                padding=dp(12), spacing=dp(8),
            )
            bg_card(vc, cr * 0.18, cg * 0.18, cb * 0.18)

            # Name row with color swatch
            nr = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
            swatch = BoxLayout(size_hint_x=None, width=dp(8))
            bg_card(swatch, cr, cg, cb)
            nr.add_widget(swatch)
            nr.add_widget(Label(
                text=f"[b]{_esc(row['name'])}[/b]",
                markup=True, color=(cr, cg, cb, 1),
                halign="left", text_size=(None, None), font_size=dp(16),
            ))
            vc.add_widget(nr)

            # Total épargné
            tr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            tr.add_widget(Label(text="Total épargné :", color=(0.75, 0.75, 0.75, 1),
                                size_hint_x=0.42, font_size=dp(12), halign="right",
                                text_size=(None, None)))
            total_inp = TextInput(
                text=f"{row['current_total']:.2f}", multiline=False,
                size_hint_x=0.42, font_size=dp(13),
                background_color=(0.12, 0.15, 0.22, 1), foreground_color=(1, 1, 1, 1),
            )
            tr.add_widget(total_inp)
            tr.add_widget(Label(text="€", color=(0.7, 0.7, 0.7, 1), size_hint_x=0.1))
            vc.add_widget(tr)

            # Versement mensuel
            mr = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            mr.add_widget(Label(text="Versement/mois :", color=(0.75, 0.75, 0.75, 1),
                                size_hint_x=0.42, font_size=dp(12), halign="right",
                                text_size=(None, None)))
            monthly_inp = TextInput(
                text=f"{row['monthly_amount']:.2f}", multiline=False,
                size_hint_x=0.42, font_size=dp(13),
                background_color=(0.12, 0.15, 0.22, 1), foreground_color=(1, 1, 1, 1),
            )
            mr.add_widget(monthly_inp)
            mr.add_widget(Label(text="€", color=(0.7, 0.7, 0.7, 1), size_hint_x=0.1))
            vc.add_widget(mr)

            btns = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(6))
            vid = row["id"]
            save_btn = Button(
                text="💾 Sauvegarder", font_size=dp(12),
                background_normal="",
                background_color=(cr * 0.7, cg * 0.7, cb * 0.7, 1),
            )
            save_btn.bind(on_press=lambda b, vid=vid, ti=total_inp, mi=monthly_inp:
                          self._save_vehicle(vid, ti.text, mi.text))
            del_btn = Button(
                text="🗑", font_size=dp(14), size_hint_x=0.2,
                background_normal="", background_color=(0.5, 0.1, 0.1, 1),
            )
            del_btn.bind(on_press=lambda b, vid=vid, vname=row["name"]:
                         self._confirm_delete(vid, vname))
            btns.add_widget(save_btn)
            btns.add_widget(del_btn)
            vc.add_widget(btns)

            self.content_area.add_widget(vc)

        add_btn = Button(
            text="➕  Ajouter un compte", font_size=dp(14),
            size_hint_y=None, height=dp(52),
            background_normal="", background_color=(0.15, 0.42, 0.15, 1),
        )
        add_btn.bind(on_press=self._show_add_vehicle)
        self.content_area.add_widget(add_btn)

    def _save_vehicle(self, vid, total_text, monthly_text):
        try:
            total   = float(total_text.replace(",", ".").replace(" ", "").replace(" ", ""))
            monthly = float(monthly_text.replace(",", ".").replace(" ", "").replace(" ", ""))
        except ValueError:
            self._popup("Erreur", "Montant invalide — ex: 743.63")
            return
        self.conn.execute(
            "UPDATE vehicles SET current_total=?, monthly_amount=? WHERE id=?",
            (total, monthly, vid),
        )
        self.conn.commit()
        self.refresh()

    def _confirm_delete(self, vid, vname):
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        content.add_widget(Label(
            text=f"Supprimer [b]{_esc(vname)}[/b] et tout son historique ?",
            markup=True, color=(1, 1, 1, 1), font_size=dp(13),
        ))
        popup = Popup(title="Confirmer la suppression", content=content, size_hint=(0.85, 0.38))
        btns = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))

        def do_delete(b):
            self.conn.execute("DELETE FROM vehicles WHERE id=?", (vid,))
            self.conn.commit()
            popup.dismiss()
            self.refresh()

        ok = Button(text="🗑 Supprimer", background_normal="",
                    background_color=(0.65, 0.1, 0.1, 1))
        ok.bind(on_press=do_delete)
        cancel = Button(text="Annuler", background_normal="",
                        background_color=(0.2, 0.2, 0.35, 1))
        cancel.bind(on_press=popup.dismiss)
        btns.add_widget(ok)
        btns.add_widget(cancel)
        content.add_widget(btns)
        popup.open()

    def _show_add_vehicle(self, _btn):
        content = BoxLayout(orientation="vertical", spacing=dp(10), padding=dp(12))
        content.add_widget(Label(
            text="[b]Nouveau compte épargne[/b]",
            markup=True, size_hint_y=None, height=dp(28), font_size=dp(15),
        ))
        name_inp    = TextInput(hint_text="Nom (ex: Livret A)", multiline=False,
                                size_hint_y=None, height=dp(44))
        monthly_inp = TextInput(hint_text="Versement mensuel (€)", multiline=False,
                                size_hint_y=None, height=dp(44))
        total_inp   = TextInput(hint_text="Total déjà épargné (€)", multiline=False,
                                size_hint_y=None, height=dp(44))
        for w in [name_inp, monthly_inp, total_inp]:
            content.add_widget(w)

        popup = Popup(title="Ajouter un compte", content=content, size_hint=(0.9, 0.62))
        btns  = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(8))

        def do_add(_b):
            name = name_inp.text.strip()
            if not name:
                return
            try:
                monthly = float(monthly_inp.text.replace(",", ".") or "0")
                total   = float(total_inp.text.replace(",", ".") or "0")
            except ValueError:
                return
            count = self.conn.execute("SELECT COUNT(*) FROM vehicles").fetchone()[0]
            self.conn.execute(
                "INSERT OR IGNORE INTO vehicles (name, monthly_amount, current_total, color_idx)"
                " VALUES (?,?,?,?)",
                (name, monthly, total, count % len(VEHICLE_COLORS)),
            )
            self.conn.commit()
            popup.dismiss()
            self.refresh()

        ok = Button(text="✅ Ajouter", background_normal="",
                    background_color=(0.15, 0.45, 0.15, 1))
        ok.bind(on_press=do_add)
        cancel = Button(text="Annuler", background_normal="",
                        background_color=(0.35, 0.1, 0.1, 1))
        cancel.bind(on_press=popup.dismiss)
        btns.add_widget(ok)
        btns.add_widget(cancel)
        content.add_widget(btns)
        popup.open()

    # ── Entry tab ─────────────────────────────────────────────────────────────

    def _tab_entry(self, rows):
        self.content_area.add_widget(Label(
            text="[b]➕ Saisir un versement mensuel[/b]",
            markup=True, color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None, height=dp(34), font_size=dp(16),
        ))

        now = datetime.now()
        entry_card = card("#0E1728", height=310, padding=14, spacing=10)

        # Vehicle
        vehicle_names = [r["name"] for r in rows]
        entry_card.add_widget(Label(
            text="Compte :", color=(0.75, 0.75, 0.75, 1),
            size_hint_y=None, height=dp(22), halign="left",
            text_size=(None, None), font_size=dp(12),
        ))
        self._entry_vehicle = Spinner(
            text=vehicle_names[0] if vehicle_names else "—",
            values=vehicle_names,
            size_hint_y=None, height=dp(46),
            background_normal="", background_color=(0.18, 0.28, 0.5, 1),
            font_size=dp(14), color=(1, 1, 1, 1),
        )
        entry_card.add_widget(self._entry_vehicle)

        # Month / year
        mr = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(6))
        self._entry_month = Spinner(
            text=MONTH_NAMES_FR[now.month],
            values=MONTH_NAMES_FR[1:],
            size_hint_x=0.65,
            background_normal="", background_color=(0.18, 0.28, 0.5, 1),
            font_size=dp(13), color=(1, 1, 1, 1),
        )
        self._entry_year = TextInput(
            text=str(now.year), multiline=False, size_hint_x=0.35,
            font_size=dp(13),
            background_color=(0.12, 0.15, 0.22, 1), foreground_color=(1, 1, 1, 1),
        )
        mr.add_widget(self._entry_month)
        mr.add_widget(self._entry_year)
        entry_card.add_widget(mr)

        # Amount
        entry_card.add_widget(Label(
            text="Montant versé (€) :", color=(0.75, 0.75, 0.75, 1),
            size_hint_y=None, height=dp(22), halign="left",
            text_size=(None, None), font_size=dp(12),
        ))
        self._entry_amount = TextInput(
            hint_text="ex: 743.63", multiline=False,
            size_hint_y=None, height=dp(50), font_size=dp(16),
            background_color=(0.12, 0.15, 0.22, 1), foreground_color=(1, 1, 1, 1),
        )
        entry_card.add_widget(self._entry_amount)

        # Note
        self._entry_note = TextInput(
            hint_text="Note (optionnel)", multiline=False,
            size_hint_y=None, height=dp(38), font_size=dp(12),
            background_color=(0.12, 0.15, 0.22, 1), foreground_color=(0.75, 0.75, 0.75, 1),
        )
        entry_card.add_widget(self._entry_note)

        save_btn = Button(
            text="💾 Enregistrer le versement", font_size=dp(14),
            size_hint_y=None, height=dp(50),
            background_normal="", background_color=(0.1, 0.45, 0.1, 1),
        )
        save_btn.bind(on_press=lambda b: self._save_entry(rows))
        entry_card.add_widget(save_btn)

        self.content_area.add_widget(entry_card)

        self.content_area.add_widget(Label(
            text="[color=#555555]💡 Chaque versement est ajouté\nau total du compte concerné.[/color]",
            markup=True, size_hint_y=None, height=dp(46),
            font_size=dp(12), halign="center",
        ))

    def _save_entry(self, rows):
        vname = self._entry_vehicle.text
        vrow  = next((r for r in rows if r["name"] == vname), None)
        if not vrow:
            self._popup("Erreur", "Sélectionnez un compte")
            return
        try:
            amount = float(self._entry_amount.text.replace(",", ".").replace(" ", "").replace(" ", ""))
            year   = int(self._entry_year.text)
        except ValueError:
            self._popup("Erreur", "Montant ou année invalide")
            return
        if amount <= 0:
            self._popup("Erreur", "Le montant doit être positif")
            return
        month_num = MONTH_NAMES_FR.index(self._entry_month.text)
        if month_num == 0:
            month_num = 1

        self.conn.execute(
            "INSERT INTO entries (vehicle_id, year, month, amount, note) VALUES (?,?,?,?,?)",
            (vrow["id"], year, month_num, amount, self._entry_note.text.strip() or None),
        )
        self.conn.execute(
            "UPDATE vehicles SET current_total = current_total + ? WHERE id=?",
            (amount, vrow["id"]),
        )
        self.conn.commit()

        self._entry_amount.text = ""
        self._entry_note.text   = ""
        self._popup("✅ Versement enregistré",
                    f"{fmt_money(amount)} ajouté à {vname}\n({MONTH_NAMES_FR[month_num]} {year})")
        self.refresh()

    # ── History tab ───────────────────────────────────────────────────────────

    def _tab_history(self):
        self.content_area.add_widget(Label(
            text="[b]📋 Historique des versements[/b]",
            markup=True, color=(0.9, 0.9, 0.9, 1),
            size_hint_y=None, height=dp(34), font_size=dp(16),
        ))

        entries = self.conn.execute("""
            SELECT e.id, e.year, e.month, e.amount, e.note, e.created_at,
                   v.name AS vname, v.color_idx
            FROM entries e
            JOIN vehicles v ON v.id = e.vehicle_id
            ORDER BY e.year DESC, e.month DESC, e.created_at DESC
            LIMIT 150
        """).fetchall()

        if not entries:
            self.content_area.add_widget(Label(
                text="[color=#555555]Aucun versement enregistré.\nUtilisez l'onglet ➕ Saisir.[/color]",
                markup=True, size_hint_y=None, height=dp(80),
                font_size=dp(14), halign="center",
            ))
            return

        # Group by month
        current_group = None
        for entry in entries:
            group_key = (entry["year"], entry["month"])
            if group_key != current_group:
                current_group = group_key
                mn = MONTH_NAMES_FR[entry["month"]] if 1 <= entry["month"] <= 12 else str(entry["month"])
                grp_total = sum(
                    e["amount"] for e in entries
                    if e["year"] == entry["year"] and e["month"] == entry["month"]
                )
                self.content_area.add_widget(Label(
                    text=f"[b]{mn} {entry['year']}[/b]  —  total {_esc(fmt_money(grp_total))}",
                    markup=True, color=(0.6, 0.6, 0.6, 1),
                    size_hint_y=None, height=dp(26), font_size=dp(12),
                ))

            cr, cg, cb = hex_to_rgb(VEHICLE_COLORS[entry["color_idx"] % len(VEHICLE_COLORS)])
            row_w = BoxLayout(
                size_hint_y=None, height=dp(56),
                padding=dp(10), spacing=dp(8),
            )
            bg_card(row_w, cr * 0.14, cg * 0.14, cb * 0.14)

            acc = BoxLayout(size_hint_x=None, width=dp(4))
            bg_card(acc, cr, cg, cb)
            row_w.add_widget(acc)

            info = BoxLayout(orientation="vertical", spacing=dp(2))
            note_str = f"  — {_esc(entry['note'])}" if entry["note"] else ""
            info.add_widget(Label(
                text=f"[b]{_esc(entry['vname'])}[/b]{note_str}",
                markup=True, color=(0.9, 0.9, 0.9, 1), halign="left",
                text_size=(None, None), size_hint_y=0.5, font_size=dp(13),
            ))
            info.add_widget(Label(
                text=f"[b][color=#81C784]{_esc(fmt_money(entry['amount']))}[/color][/b]",
                markup=True, halign="left",
                text_size=(None, None), size_hint_y=0.5, font_size=dp(14),
            ))
            row_w.add_widget(info)

            eid = entry["id"]
            del_btn = Button(
                text="✕", size_hint_x=None, width=dp(38),
                font_size=dp(14), background_normal="",
                background_color=(0.45, 0.1, 0.1, 1),
            )
            del_btn.bind(on_press=lambda b, eid=eid, amt=entry["amount"], vid=entry["vname"]:
                         self._delete_entry(eid, amt))
            row_w.add_widget(del_btn)
            self.content_area.add_widget(row_w)

    def _delete_entry(self, entry_id, amount):
        # Get vehicle_id before deleting
        row = self.conn.execute("SELECT vehicle_id FROM entries WHERE id=?", (entry_id,)).fetchone()
        if not row:
            return
        self.conn.execute("DELETE FROM entries WHERE id=?", (entry_id,))
        self.conn.execute(
            "UPDATE vehicles SET current_total = MAX(0, current_total - ?) WHERE id=?",
            (amount, row["vehicle_id"]),
        )
        self.conn.commit()
        self.refresh()

    # ── Utilities ─────────────────────────────────────────────────────────────

    def _popup(self, title, text):
        content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
        content.add_widget(Label(
            text=_esc(text), markup=False, color=(1, 1, 1, 1),
            font_size=dp(13), halign="center",
        ))
        popup = Popup(title=title, content=content, size_hint=(0.82, 0.38))
        ok = Button(text="OK", size_hint_y=None, height=dp(44),
                    background_normal="", background_color=(0.2, 0.35, 0.6, 1))
        ok.bind(on_press=popup.dismiss)
        content.add_widget(ok)
        popup.open()

    def on_stop(self):
        if self.conn:
            self.conn.close()


if __name__ == "__main__":
    SavingsApp().run()
