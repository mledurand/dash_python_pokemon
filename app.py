# ==============================================================================
# POKÉDEX ANALYTICS — APPLICATION PYTHON DASH
# Exécution : python app.py (puis ouvrir http://127.0.0.1:8050)
# ==============================================================================
# Liens directs pour téléchargement manuel des données :
# - CSV Stats (GitHub)      : https://raw.githubusercontent.com/KeithGalli/pandas/master/pokemon_data.csv
# - CSV Noms FR (Veekun)    : https://raw.githubusercontent.com/veekun/pokedex/master/pokedex/data/csv/pokemon_species_names.csv
# - CSV Alternatif (GitHub) : https://raw.githubusercontent.com/lgreski/pokemonData/master/Pokemon.csv
# - Kaggle Dataset          : https://www.kaggle.com/datasets/abcsds/pokemon
# - Open Data FR (JSON)     : https://tyradex.vercel.app/api/v1/pokemon
# ==============================================================================

import base64
import io
import re
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import Dash, Input, Output, State, dash_table, dcc, html, no_update
import dash_bootstrap_components as dbc

# ------------------------------------------------------------------------------
# 1. CONSTANTES VISUELLES & DICTIONNAIRES POKÉMON
# ------------------------------------------------------------------------------

COULEURS_TYPES = {
    "Normal": "#A8A77A",
    "Feu": "#EE8130",
    "Eau": "#6390F0",
    "Électrik": "#F7D02C",
    "Plante": "#7AC74C",
    "Glace": "#96D9D6",
    "Combat": "#C22E28",
    "Poison": "#A33EA1",
    "Sol": "#E2BF65",
    "Vol": "#A98FF3",
    "Psy": "#F95587",
    "Insecte": "#A6B91A",
    "Roche": "#B6A136",
    "Spectre": "#735797",
    "Dragon": "#6F35FC",
    "Ténèbres": "#705746",
    "Acier": "#B7B7CE",
    "Fée": "#D685AD",
    "Aucun": "#94A3B8",
}

TYPES_CLAIRS = {"Électrik", "Glace", "Sol", "Normal", "Acier"}

TRADUCTION_TYPES = {
    "Normal": "Normal", "Fire": "Feu", "Water": "Eau",
    "Electric": "Électrik", "Grass": "Plante", "Ice": "Glace",
    "Fighting": "Combat", "Poison": "Poison", "Ground": "Sol",
    "Flying": "Vol", "Psychic": "Psy", "Bug": "Insecte",
    "Rock": "Roche", "Ghost": "Spectre", "Dragon": "Dragon",
    "Dark": "Ténèbres", "Steel": "Acier", "Fairy": "Fée",
}

STATS_COLS = ["PV", "Attaque", "Defense", "Attaque_Spe", "Defense_Spe", "Vitesse"]
STATS_LABELS = {
    "PV": "PV",
    "Attaque": "Attaque",
    "Defense": "Défense",
    "Attaque_Spe": "Att. Spé.",
    "Defense_Spe": "Déf. Spé.",
    "Vitesse": "Vitesse",
    "Total": "Total",
}

PALETTE_STATS = {
    "PV": "#22C55E",
    "Attaque": "#EF4444",
    "Défense": "#F59E0B",
    "Att. Spé.": "#3B82F6",
    "Déf. Spé.": "#8B5CF6",
    "Vitesse": "#EC4899",
}

# ------------------------------------------------------------------------------
# 2. ÉCHANTILLON DE SECOURS HORS-LIGNE (20 POKÉMON EMBLÉMATIQUES)
# ------------------------------------------------------------------------------


def creer_echantillon_secours() -> pd.DataFrame:
    donnees = [
        (3, "Florizarre", "Plante", "Poison", 80, 82, 83, 100, 100, 80, 1, False),
        (6, "Dracaufeu", "Feu", "Vol", 78, 84, 78, 109, 85, 100, 1, False),
        (9, "Tortank", "Eau", "Aucun", 79, 83, 100, 85, 105, 78, 1, False),
        (25, "Pikachu", "Électrik", "Aucun", 35, 55, 40, 50, 50, 90, 1, False),
        (94, "Ectoplasma", "Spectre", "Poison", 60, 65, 60, 130, 75, 110, 1, False),
        (133, "Évoli", "Normal", "Aucun", 55, 55, 50, 45, 65, 55, 1, False),
        (143, "Ronflex", "Normal", "Aucun", 160, 110, 65, 65, 110, 30, 1, False),
        (145, "Électhor", "Électrik", "Vol", 90, 90, 85, 125, 90, 100, 1, True),
        (149, "Dracolosse", "Dragon", "Vol", 91, 134, 95, 100, 100, 80, 1, False),
        (150, "Mewtwo", "Psy", "Aucun", 106, 110, 90, 154, 90, 130, 1, True),
        (212, "Cizayox", "Insecte", "Acier", 70, 130, 100, 55, 80, 65, 2, False),
        (248, "Tyranocif", "Roche", "Ténèbres", 100, 134, 110, 95, 100, 61, 2, False),
        (249, "Lugia", "Psy", "Vol", 106, 90, 130, 90, 154, 110, 2, True),
        (282, "Gardevoir", "Psy", "Fée", 68, 65, 65, 125, 115, 80, 3, False),
        (376, "Métalosse", "Acier", "Psy", 80, 135, 130, 95, 90, 70, 3, False),
        (384, "Rayquaza", "Dragon", "Vol", 105, 150, 90, 150, 90, 95, 3, True),
        (445, "Carchacrok", "Dragon", "Sol", 108, 130, 95, 80, 85, 102, 4, False),
        (448, "Lucario", "Combat", "Acier", 70, 110, 70, 115, 70, 90, 4, False),
        (493, "Arceus", "Normal", "Aucun", 120, 120, 120, 120, 120, 120, 4, True),
        (658, "Amphinobi", "Eau", "Ténèbres", 72, 95, 67, 103, 71, 122, 6, False),
    ]
    df = pd.DataFrame(
        donnees,
        columns=[
            "ID", "Nom", "Type1", "Type2", "PV", "Attaque", "Defense",
            "Attaque_Spe", "Defense_Spe", "Vitesse", "Generation", "Legendaire",
        ],
    )
    df["Total"] = df[STATS_COLS].sum(axis=1)
    return df


# ------------------------------------------------------------------------------
# 3. STANDARDISATION & ACQUISITION AUTOMATIQUE DES DONNÉES
# ------------------------------------------------------------------------------


def _normaliser_nom_col(nom: str) -> str:
    return re.sub(r"[^a-z0-9]", "", str(nom).lower())


def _trouver_colonne(cols, candidats):
    mapping = {_normaliser_nom_col(c): c for c in cols}
    for cand in candidats:
        cle = _normaliser_nom_col(cand)
        if cle in mapping:
            return mapping[cle]
    return None


def _traduire_serie_types(serie: pd.Series) -> pd.Series:
    s = serie.fillna("Aucun").astype(str).str.strip()
    s = s.replace({"": "Aucun", "nan": "Aucun", "None": "Aucun", "NaN": "Aucun"})
    return s.map(lambda v: TRADUCTION_TYPES.get(v, v))


def _dedupliquer_noms(serie: pd.Series) -> pd.Series:
    compteur = {}
    resultat = []
    for nom in serie.astype(str):
        if nom not in compteur:
            compteur[nom] = 1
            resultat.append(nom)
        else:
            compteur[nom] += 1
            resultat.append(f"{nom} (Forme {compteur[nom]})")
    return pd.Series(resultat, index=serie.index)


def standardiser_pokedex(df: pd.DataFrame) -> pd.DataFrame:
    cols = list(df.columns)
    col_id = _trouver_colonne(cols, ["id", "#", "pokedex_number", "number", "numero"])
    col_nom = _trouver_colonne(cols, ["nom", "name", "nom_fr", "french_name", "pokemon"])
    col_t1 = _trouver_colonne(cols, ["type1", "type 1", "type_1", "type"])
    col_t2 = _trouver_colonne(cols, ["type2", "type 2", "type_2"])
    col_pv = _trouver_colonne(cols, ["pv", "hp"])
    col_atk = _trouver_colonne(cols, ["attaque", "attack", "atk"])
    col_def = _trouver_colonne(cols, ["defense", "défense", "def"])
    col_spa = _trouver_colonne(cols, ["attaque_spe", "sp. atk", "sp_atk", "spattack", "sp_attack", "att_spe"])
    col_spd = _trouver_colonne(cols, ["defense_spe", "sp. def", "sp_def", "spdefense", "sp_defense", "def_spe"])
    col_vit = _trouver_colonne(cols, ["vitesse", "speed", "vit"])
    col_tot = _trouver_colonne(cols, ["total", "base_total", "somme"])
    col_gen = _trouver_colonne(cols, ["generation", "génération", "gen"])
    col_leg = _trouver_colonne(cols, ["legendaire", "légendaire", "legendary", "is_legendary"])

    requis = [col_nom, col_t1, col_pv, col_atk, col_def, col_spa, col_spd, col_vit]
    if any(c is None for c in requis):
        raise ValueError(
            "Colonnes essentielles manquantes (Nom, Type 1, PV, Attaque, Défense, Att. Spé., Déf. Spé., Vitesse)."
        )

    out = pd.DataFrame()
    out["ID"] = pd.to_numeric(df[col_id], errors="coerce") if col_id else range(1, len(df) + 1)
    out["ID"] = out["ID"].fillna(pd.Series(range(1, len(df) + 1))).astype(int)
    out["Nom"] = df[col_nom].astype(str).str.strip()
    out["Type1"] = _traduire_serie_types(df[col_t1])
    out["Type2"] = _traduire_serie_types(df[col_t2]) if col_t2 else "Aucun"

    for col_cible, col_src in [
        ("PV", col_pv),
        ("Attaque", col_atk),
        ("Defense", col_def),
        ("Attaque_Spe", col_spa),
        ("Defense_Spe", col_spd),
        ("Vitesse", col_vit),
    ]:
        out[col_cible] = pd.to_numeric(df[col_src], errors="coerce")

    out["Generation"] = (
        pd.to_numeric(df[col_gen], errors="coerce").fillna(1).astype(int) if col_gen else 1
    )

    if col_leg:
        out["Legendaire"] = (
            df[col_leg].astype(str).str.strip().str.lower().isin(["true", "t", "1", "oui", "yes"])
        )
    else:
        out["Legendaire"] = False

    out = out.dropna(subset=["Nom"] + STATS_COLS).copy()
    for c in STATS_COLS:
        out[c] = out[c].astype(int)

    if col_tot:
        tot_num = pd.to_numeric(df.loc[out.index, col_tot], errors="coerce")
        out["Total"] = tot_num.fillna(out[STATS_COLS].sum(axis=1)).astype(int)
    else:
        out["Total"] = out[STATS_COLS].sum(axis=1).astype(int)

    out["Nom"] = _dedupliquer_noms(out["Nom"])
    return out.reset_index(drop=True)


def _telecharger_csv(url: str, timeout: int = 8) -> pd.DataFrame:
    resp = requests.get(url, timeout=timeout)
    resp.raise_for_status()
    return pd.read_csv(io.StringIO(resp.text))


def charger_pokedex_auto():
    url_stats_en = "https://raw.githubusercontent.com/KeithGalli/pandas/master/pokemon_data.csv"
    url_noms_fr = "https://raw.githubusercontent.com/veekun/pokedex/master/pokedex/data/csv/pokemon_species_names.csv"
    url_fallback_2 = "https://raw.githubusercontent.com/lgreski/pokemonData/master/Pokemon.csv"

    # 1. Priorité en ligne : Stats GitHub + Noms officiels FR (Veekun)
    try:
        df_base = standardiser_pokedex(_telecharger_csv(url_stats_en))
        df_fr = _telecharger_csv(url_noms_fr)
        df_fr = (
            df_fr[df_fr["local_language_id"] == 5][["pokemon_species_id", "name"]]
            .drop_duplicates(subset=["pokemon_species_id"])
            .rename(columns={"pokemon_species_id": "ID", "name": "Nom_FR"})
        )
        merged = df_base.merge(df_fr, on="ID", how="left")

        def formater_nom_fr(row):
            if pd.isna(row["Nom_FR"]):
                return row["Nom"]
            nom_en = str(row["Nom"])
            suffixe = ""
            if "Mega " in nom_en and nom_en.endswith(" X"):
                suffixe = " (Méga X)"
            elif "Mega " in nom_en and nom_en.endswith(" Y"):
                suffixe = " (Méga Y)"
            elif "Mega " in nom_en:
                suffixe = " (Méga)"
            elif "Primal " in nom_en:
                suffixe = " (Primo)"
            return f"{row['Nom_FR']}{suffixe}"

        merged["Nom"] = merged.apply(formater_nom_fr, axis=1)
        merged["Nom"] = _dedupliquer_noms(merged["Nom"])
        merged = merged.drop(columns=["Nom_FR"])
        if len(merged) > 50:
            return merged, "En ligne — Pokédex FR (GitHub + Veekun)"
    except Exception:
        pass

    # 2. Repli en ligne : CSV public en anglais (types traduits en français)
    for url in (url_stats_en, url_fallback_2):
        try:
            df_en = standardiser_pokedex(_telecharger_csv(url))
            if len(df_en) > 50:
                return df_en, "En ligne — Repli CSV EN (types FR)"
        except Exception:
            continue

    # 3. Échantillon de secours intégré (hors-ligne)
    return creer_echantillon_secours(), "Secours intégré (mode hors-ligne)"


DF_INIT, SOURCE_INIT = charger_pokedex_auto()

# ------------------------------------------------------------------------------
# 4. INITIALISATION DASH & STYLE POKÉDEX MODERNE
# ------------------------------------------------------------------------------

app = Dash(
    __name__,
    external_stylesheets=[dbc.themes.FLATLY, dbc.icons.FONT_AWESOME],
    title="Pokédex Analytics — Python Dash",
)

# CSS embarqué pour un fichier unique autonome (sans dossier assets/)
app.index_string = """
<!DOCTYPE html>
<html lang="fr">
  <head>
    {%metas%}
    <title>{%title%}</title>
    {%favicon%}
    {%css%}
    <style>
      body { background-color: #F4F6FA; color: #1E293B; font-family: 'Segoe UI', system-ui, sans-serif; }
      .pokedex-navbar {
        background: linear-gradient(90deg, #DC0A2D 0%, #990820 100%);
        border-bottom: 4px solid #1E293B;
        box-shadow: 0 3px 10px rgba(0,0,0,0.15);
      }
      .pokeball-dot {
        width: 22px; height: 22px; border-radius: 50%; display: inline-block;
        background: linear-gradient(180deg, #FFF 0%, #FFF 45%, #1E293B 45%, #1E293B 55%, #DC0A2D 55%, #DC0A2D 100%);
        border: 2px solid #FFFFFF; margin-right: 10px; vertical-align: middle;
      }
      .sidebar-card {
        background: #FFFFFF; border-radius: 14px; border: 1px solid #E2E8F0;
        box-shadow: 0 4px 12px rgba(15,23,42,0.06); padding: 18px;
      }
      .kpi-card {
        background: #FFFFFF; border-radius: 14px; border: 1px solid #E2E8F0;
        border-left: 5px solid #DC0A2D; box-shadow: 0 4px 12px rgba(15,23,42,0.06);
        padding: 14px 18px; height: 100%;
      }
      .kpi-blue { border-left-color: #2A75BB; }
      .kpi-amber { border-left-color: #F59E0B; }
      .kpi-purple { border-left-color: #7C3AED; }
      .kpi-title { font-size: 0.8rem; text-transform: uppercase; letter-spacing: 0.5px; color: #64748B; font-weight: 700; }
      .kpi-value { font-size: 1.55rem; font-weight: 800; color: #0F172A; margin-top: 4px; }
      .dash-card {
        background: #FFFFFF; border-radius: 14px; border: 1px solid #E2E8F0;
        box-shadow: 0 4px 14px rgba(15,23,42,0.05); padding: 16px;
      }
      .type-pill {
        display: inline-block; padding: 3px 10px; border-radius: 999px;
        font-size: 0.78rem; font-weight: 700; text-transform: uppercase;
      }
      .faceoff-banner {
        background: linear-gradient(135deg, #1E293B 0%, #334155 100%);
        color: #FFFFFF; border-radius: 12px; padding: 14px 18px; margin-bottom: 14px;
      }
      .upload-zone {
        border: 2px dashed #CBD5E1; border-radius: 10px; padding: 10px;
        text-align: center; cursor: pointer; background: #F8FAFC; font-size: 0.85rem;
      }
      .upload-zone:hover { border-color: #DC0A2D; background: #FFF5F5; }
    </style>
  </head>
  <body>
    {%app_entry%}
    <footer>{%config%}{%scripts%}{%renderer%}</footer>
  </body>
</html>
"""


def _generer_styles_badges_tableau():
    styles = []
    for t, couleur in COULEURS_TYPES.items():
        texte = "#1E293B" if t in TYPES_CLAIRS else "#FFFFFF"
        for col in ("Type1", "Type2"):
            styles.append(
                {
                    "if": {"filter_query": f'{{{col}}} = "{t}"', "column_id": col},
                    "backgroundColor": couleur,
                    "color": texte,
                    "fontWeight": "700",
                    "textAlign": "center",
                    "borderRadius": "6px",
                }
            )
    return styles


def _badge_type_html(t: str):
    couleur = COULEURS_TYPES.get(t, "#64748B")
    texte = "#1E293B" if t in TYPES_CLAIRS else "#FFFFFF"
    return html.Span(t, className="type-pill ms-2", style={"backgroundColor": couleur, "color": texte})


def _figure_vide(message: str = "Aucun Pokémon ne correspond aux filtres actifs."):
    fig = go.Figure()
    fig.add_annotation(text=message, showarrow=False, font=dict(size=14, color="#64748B"))
    fig.update_layout(
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


# ------------------------------------------------------------------------------
# 5. LAYOUT RESPONSIVE
# ------------------------------------------------------------------------------

min_tot_init = int(DF_INIT["Total"].min())
max_tot_init = int(DF_INIT["Total"].max())
noms_init = sorted(DF_INIT["Nom"].unique())
p1_init = "Dracaufeu" if "Dracaufeu" in noms_init else noms_init[0]
p2_init = "Tortank" if "Tortank" in noms_init else noms_init[min(1, len(noms_init) - 1)]

navbar = dbc.Navbar(
    dbc.Container(
        [
            html.Div(
                [
                    html.Span(className="pokeball-dot"),
                    html.Span(
                        "POKÉDEX ANALYTICS — PYTHON DASH",
                        style={"fontWeight": "800", "color": "#FFFFFF", "fontSize": "1.2rem", "letterSpacing": "0.5px"},
                    ),
                ],
                className="d-flex align-items-center",
            ),
            html.Span(
                id="header-source-badge",
                children=f"Source : {SOURCE_INIT}",
                className="badge bg-light text-dark px-3 py-2",
            ),
        ],
        fluid=True,
    ),
    className="pokedex-navbar mb-3 py-2",
)

sidebar = html.Div(
    className="sidebar-card",
    children=[
        html.H5([html.I(className="fa-solid fa-sliders me-2 text-danger"), "Filtres Pokédex"], className="fw-bold mb-3"),
        dbc.Label("Type principal (Type 1)", className="fw-semibold small"),
        dcc.Dropdown(
            id="filtre-type1",
            options=[{"label": t, "value": t} for t in sorted(DF_INIT["Type1"].unique())],
            multi=True,
            placeholder="Tous les types",
            className="mb-3",
        ),
        dbc.Label("Type secondaire (Type 2)", className="fw-semibold small"),
        dcc.Dropdown(
            id="filtre-type2",
            options=[{"label": t, "value": t} for t in sorted(DF_INIT["Type2"].unique())],
            multi=True,
            placeholder="Tous (y compris Aucun)",
            className="mb-3",
        ),
        dbc.Label("Génération(s)", className="fw-semibold small"),
        dcc.Dropdown(
            id="filtre-gen",
            options=[{"label": f"Génération {g}", "value": int(g)} for g in sorted(DF_INIT["Generation"].unique())],
            multi=True,
            placeholder="Toutes les générations",
            className="mb-3",
        ),
        dbc.Switch(
            id="filtre-legendaire",
            label="Légendaires / Mythiques uniquement",
            value=False,
            className="mb-3 fw-semibold",
        ),
        dbc.Label("Intervalle de stat Total", className="fw-semibold small"),
        dcc.RangeSlider(
            id="filtre-total",
            min=min_tot_init,
            max=max_tot_init,
            step=5,
            value=[min_tot_init, max_tot_init],
            marks={min_tot_init: str(min_tot_init), max_tot_init: str(max_tot_init)},
            tooltip={"placement": "bottom", "always_visible": False},
            className="mb-3",
        ),
        dbc.Button(
            [html.I(className="fa-solid fa-rotate-left me-2"), "Réinitialiser les filtres"],
            id="btn-reset",
            color="danger",
            outline=True,
            size="sm",
            className="w-100 mb-3",
        ),
        html.Hr(),
        html.H6([html.I(className="fa-solid fa-upload me-2"), "Importer un CSV local"], className="fw-bold"),
        dcc.Upload(
            id="upload-csv",
            children=html.Div(["Glisser-déposer ou ", html.B("cliquer pour choisir un CSV")]),
            className="upload-zone mb-2",
            multiple=False,
        ),
        html.Div(id="upload-feedback", className="small text-muted"),
    ],
)

kpi_row = dbc.Row(
    [
        dbc.Col(
            html.Div(
                className="kpi-card",
                children=[
                    html.Div([html.I(className="fa-solid fa-dragon me-2 text-danger"), "Pokémon filtrés"], className="kpi-title"),
                    html.Div(id="kpi-count", className="kpi-value"),
                ],
            ),
            md=3, sm=6, className="mb-3",
        ),
        dbc.Col(
            html.Div(
                className="kpi-card kpi-blue",
                children=[
                    html.Div([html.I(className="fa-solid fa-chart-line me-2 text-primary"), "Moyenne stat Total"], className="kpi-title"),
                    html.Div(id="kpi-total-moy", className="kpi-value"),
                ],
            ),
            md=3, sm=6, className="mb-3",
        ),
        dbc.Col(
            html.Div(
                className="kpi-card kpi-amber",
                children=[
                    html.Div([html.I(className="fa-solid fa-bolt me-2 text-warning"), "Record Attaque / Vitesse"], className="kpi-title"),
                    html.Div(id="kpi-record", className="mt-1"),
                ],
            ),
            md=3, sm=6, className="mb-3",
        ),
        dbc.Col(
            html.Div(
                className="kpi-card kpi-purple",
                children=[
                    html.Div([html.I(className="fa-solid fa-crown me-2", style={"color": "#7C3AED"}), "Part de Légendaires"], className="kpi-title"),
                    html.Div(id="kpi-pct-leg", className="kpi-value"),
                ],
            ),
            md=3, sm=6, className="mb-3",
        ),
    ]
)

tabs_section = dbc.Tabs(
    [
        dbc.Tab(
            label="Vue analytique",
            tab_id="tab-analytique",
            children=dbc.Row(
                [
                    dbc.Col(
                        html.Div(
                            className="dash-card mt-3",
                            children=[
                                html.Div(
                                    className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2",
                                    children=[
                                        html.H6("Profil moyen des 6 statistiques", className="fw-bold m-0"),
                                        dbc.RadioItems(
                                            id="axe-synthese",
                                            options=[
                                                {"label": "Par Type", "value": "Type1"},
                                                {"label": "Par Génération", "value": "Generation"},
                                            ],
                                            value="Type1",
                                            inline=True,
                                            className="small fw-semibold",
                                        ),
                                    ],
                                ),
                                dcc.Graph(id="graph-synthese", style={"height": "430px"}),
                            ],
                        ),
                        lg=6, className="mb-3",
                    ),
                    dbc.Col(
                        html.Div(
                            className="dash-card mt-3",
                            children=[
                                html.Div(
                                    className="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-2",
                                    children=[
                                        html.H6("Nuage de points interactif", className="fw-bold m-0"),
                                        html.Div(
                                            className="d-flex gap-2",
                                            children=[
                                                dcc.Dropdown(
                                                    id="scatter-x",
                                                    options=[
                                                        {"label": "Attaque", "value": "Attaque"},
                                                        {"label": "Vitesse", "value": "Vitesse"},
                                                        {"label": "PV", "value": "PV"},
                                                        {"label": "Att. Spé.", "value": "Attaque_Spe"},
                                                    ],
                                                    value="Attaque",
                                                    clearable=False,
                                                    style={"width": "125px", "fontSize": "0.85rem"},
                                                ),
                                                dcc.Dropdown(
                                                    id="scatter-y",
                                                    options=[
                                                        {"label": "Défense", "value": "Defense"},
                                                        {"label": "Total", "value": "Total"},
                                                        {"label": "Déf. Spé.", "value": "Defense_Spe"},
                                                        {"label": "Vitesse", "value": "Vitesse"},
                                                    ],
                                                    value="Defense",
                                                    clearable=False,
                                                    style={"width": "125px", "fontSize": "0.85rem"},
                                                ),
                                            ],
                                        ),
                                    ],
                                ),
                                dcc.Graph(id="graph-scatter", style={"height": "430px"}),
                            ],
                        ),
                        lg=6, className="mb-3",
                    ),
                ]
            ),
        ),
        dbc.Tab(
            label="Base Pokédex",
            tab_id="tab-table",
            children=html.Div(
                className="dash-card mt-3",
                children=[
                    html.H6("Tableau interactif (triable, paginé, recherchable et badges par type)", className="fw-bold mb-3"),
                    dash_table.DataTable(
                        id="table-pokedex",
                        columns=[
                            {"name": "#", "id": "ID", "type": "numeric"},
                            {"name": "Nom", "id": "Nom", "type": "text"},
                            {"name": "Type 1", "id": "Type1", "type": "text"},
                            {"name": "Type 2", "id": "Type2", "type": "text"},
                            {"name": "Total", "id": "Total", "type": "numeric"},
                            {"name": "PV", "id": "PV", "type": "numeric"},
                            {"name": "Attaque", "id": "Attaque", "type": "numeric"},
                            {"name": "Défense", "id": "Defense", "type": "numeric"},
                            {"name": "Att. Spé.", "id": "Attaque_Spe", "type": "numeric"},
                            {"name": "Déf. Spé.", "id": "Defense_Spe", "type": "numeric"},
                            {"name": "Vitesse", "id": "Vitesse", "type": "numeric"},
                            {"name": "Gén.", "id": "Generation", "type": "numeric"},
                            {"name": "Légendaire", "id": "Legendaire_Txt", "type": "text"},
                        ],
                        page_size=12,
                        sort_action="native",
                        filter_action="native",
                        style_table={"overflowX": "auto"},
                        style_header={
                            "backgroundColor": "#1E293B",
                            "color": "#FFFFFF",
                            "fontWeight": "700",
                            "textAlign": "center",
                        },
                        style_cell={
                            "padding": "8px 10px",
                            "fontFamily": "'Segoe UI', sans-serif",
                            "fontSize": "0.88rem",
                            "border": "1px solid #F1F5F9",
                        },
                        style_data_conditional=_generer_styles_badges_tableau(),
                    ),
                ],
            ),
        ),
        dbc.Tab(
            label="Face-off (Duel)",
            tab_id="tab-duel",
            children=html.Div(
                className="dash-card mt-3",
                children=[
                    html.H6("Comparateur tête-à-tête de 2 Pokémon", className="fw-bold mb-3"),
                    dbc.Row(
                        [
                            dbc.Col(
                                [
                                    dbc.Label("Combattant 1 (Rouge Pokéball)", className="fw-semibold text-danger small"),
                                    dcc.Dropdown(
                                        id="duel-p1",
                                        options=[{"label": n, "value": n} for n in noms_init],
                                        value=p1_init,
                                        clearable=False,
                                    ),
                                ],
                                md=6, className="mb-3",
                            ),
                            dbc.Col(
                                [
                                    dbc.Label("Combattant 2 (Bleu Azur)", className="fw-semibold text-primary small"),
                                    dcc.Dropdown(
                                        id="duel-p2",
                                        options=[{"label": n, "value": n} for n in noms_init],
                                        value=p2_init,
                                        clearable=False,
                                    ),
                                ],
                                md=6, className="mb-3",
                            ),
                        ]
                    ),
                    html.Div(id="duel-banniere"),
                    dbc.Row(
                        [
                            dbc.Col(dcc.Graph(id="graph-duel-radar", style={"height": "420px"}), lg=6),
                            dbc.Col(dcc.Graph(id="graph-duel-barres", style={"height": "420px"}), lg=6),
                        ]
                    ),
                ],
            ),
        ),
    ],
    active_tab="tab-analytique",
)

app.layout = html.Div(
    [
        dcc.Store(id="store-pokedex", data=DF_INIT.to_dict("records")),
        navbar,
        dbc.Container(
            dbc.Row(
                [
                    dbc.Col(sidebar, lg=3, className="mb-4"),
                    dbc.Col([kpi_row, tabs_section], lg=9),
                ]
            ),
            fluid=True,
            className="pb-4",
        ),
    ]
)

# ------------------------------------------------------------------------------
# 6. CALLBACKS INTERACTIFS
# ------------------------------------------------------------------------------


@app.callback(
    Output("store-pokedex", "data"),
    Output("header-source-badge", "children"),
    Output("upload-feedback", "children"),
    Output("filtre-type1", "options"),
    Output("filtre-type2", "options"),
    Output("filtre-gen", "options"),
    Output("filtre-total", "min"),
    Output("filtre-total", "max"),
    Output("filtre-total", "marks"),
    Output("duel-p1", "options"),
    Output("duel-p2", "options"),
    Output("duel-p1", "value"),
    Output("duel-p2", "value"),
    Input("upload-csv", "contents"),
    State("upload-csv", "filename"),
    prevent_initial_call=True,
)
def gerer_upload_csv(contents, filename):
    if not contents:
        return (no_update,) * 13
    try:
        _, content_string = contents.split(",")
        decoded = base64.b64decode(content_string)
        try:
            df_raw = pd.read_csv(io.StringIO(decoded.decode("utf-8-sig")))
        except UnicodeDecodeError:
            df_raw = pd.read_csv(io.StringIO(decoded.decode("latin-1")))

        df_clean = standardiser_pokedex(df_raw)
        opt_t1 = [{"label": t, "value": t} for t in sorted(df_clean["Type1"].unique())]
        opt_t2 = [{"label": t, "value": t} for t in sorted(df_clean["Type2"].unique())]
        opt_gen = [{"label": f"Génération {g}", "value": int(g)} for g in sorted(df_clean["Generation"].unique())]
        min_t, max_t = int(df_clean["Total"].min()), int(df_clean["Total"].max())
        marks = {min_t: str(min_t), max_t: str(max_t)}
        noms = sorted(df_clean["Nom"].unique())
        opt_noms = [{"label": n, "value": n} for n in noms]
        p1 = noms[0]
        p2 = noms[min(1, len(noms) - 1)]

        return (
            df_clean.to_dict("records"),
            f"Source : Fichier local ({filename})",
            dbc.Alert(f"{len(df_clean)} Pokémon chargés depuis {filename}.", color="success", className="py-1 px-2 m-0"),
            opt_t1, opt_t2, opt_gen, min_t, max_t, marks, opt_noms, opt_noms, p1, p2,
        )
    except Exception as exc:
        return (
            no_update, no_update,
            dbc.Alert(f"Erreur CSV : {exc}", color="danger", className="py-1 px-2 m-0"),
            no_update, no_update, no_update, no_update, no_update, no_update,
            no_update, no_update, no_update, no_update,
        )


@app.callback(
    Output("filtre-type1", "value"),
    Output("filtre-type2", "value"),
    Output("filtre-gen", "value"),
    Output("filtre-legendaire", "value"),
    Output("filtre-total", "value"),
    Input("btn-reset", "n_clicks"),
    Input("store-pokedex", "data"),
    prevent_initial_call=True,
)
def reinitialiser_filtres(_, data):
    df = pd.DataFrame(data)
    return [], [], [], False, [int(df["Total"].min()), int(df["Total"].max())]


@app.callback(
    Output("kpi-count", "children"),
    Output("kpi-total-moy", "children"),
    Output("kpi-record", "children"),
    Output("kpi-pct-leg", "children"),
    Output("graph-synthese", "figure"),
    Output("graph-scatter", "figure"),
    Output("table-pokedex", "data"),
    Input("store-pokedex", "data"),
    Input("filtre-type1", "value"),
    Input("filtre-type2", "value"),
    Input("filtre-gen", "value"),
    Input("filtre-legendaire", "value"),
    Input("filtre-total", "value"),
    Input("axe-synthese", "value"),
    Input("scatter-x", "value"),
    Input("scatter-y", "value"),
)
def mettre_a_jour_dashboard(data, t1, t2, gens, leg_only, total_range, axe_synthese, scatter_x, scatter_y):
    df = pd.DataFrame(data)
    if t1:
        df = df[df["Type1"].isin(t1)]
    if t2:
        df = df[df["Type2"].isin(t2)]
    if gens:
        df = df[df["Generation"].isin(gens)]
    if leg_only:
        df = df[df["Legendaire"]]
    if total_range:
        df = df[(df["Total"] >= total_range[0]) & (df["Total"] <= total_range[1])]

    if df.empty:
        vide = _figure_vide()
        return "0", "—", "—", "0 %", vide, vide, []

    # --- KPI ---
    kpi_count = f"{len(df):,}".replace(",", " ")
    kpi_total = f"{df['Total'].mean():.1f}"
    top_atk = df.loc[df["Attaque"].idxmax()]
    top_vit = df.loc[df["Vitesse"].idxmax()]
    kpi_record = html.Div(
        [
            html.Div(f"Atk {int(top_atk['Attaque'])} ({top_atk['Nom']})", style={"fontWeight": "800", "fontSize": "1.02rem"}),
            html.Div(f"Vit {int(top_vit['Vitesse'])} ({top_vit['Nom']})", style={"color": "#64748B", "fontSize": "0.85rem"}),
        ]
    )
    kpi_pct_leg = f"{100 * df['Legendaire'].mean():.1f} %"

    # --- GRAPHIQUE 1 : PROFIL MOYEN DES 6 STATS ---
    df_grp = df.copy()
    df_grp["Groupe"] = df_grp["Generation"].map(lambda g: f"Gén. {g}") if axe_synthese == "Generation" else df_grp["Type1"]
    agg = df_grp.groupby("Groupe", as_index=False)[STATS_COLS + ["Total"]].mean().sort_values("Total", ascending=False)
    long_df = agg.melt(id_vars="Groupe", value_vars=STATS_COLS, var_name="Stat", value_name="Moyenne")
    long_df["Stat_Label"] = long_df["Stat"].map(STATS_LABELS)

    fig_synthese = px.bar(
        long_df,
        x="Groupe",
        y="Moyenne",
        color="Stat_Label",
        color_discrete_map=PALETTE_STATS,
        barmode="stack",
        labels={"Groupe": "", "Moyenne": "Somme des moyennes (Total moyen)", "Stat_Label": "Statistique"},
    )
    fig_synthese.update_layout(
        xaxis_tickangle=-35,
        legend=dict(orientation="h", y=1.14, x=0, title_text=""),
        margin=dict(l=40, r=15, t=45, b=75),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # --- GRAPHIQUE 2 : NUAGE DE POINTS INTERACTIF ---
    fig_scatter = px.scatter(
        df,
        x=scatter_x,
        y=scatter_y,
        color="Type1",
        color_discrete_map=COULEURS_TYPES,
        hover_name="Nom",
        hover_data={
            "ID": True,
            "Type1": True,
            "Type2": True,
            "Total": True,
            "PV": True,
            "Attaque": True,
            "Defense": True,
            "Vitesse": True,
            "Generation": True,
        },
        labels={scatter_x: STATS_LABELS[scatter_x], scatter_y: STATS_LABELS[scatter_y], "Type1": "Type 1"},
    )
    fig_scatter.update_traces(marker=dict(size=10, opacity=0.85, line=dict(width=1, color="#FFFFFF")))
    fig_scatter.update_layout(
        margin=dict(l=40, r=15, t=20, b=40),
        xaxis=dict(gridcolor="#E2E8F0"),
        yaxis=dict(gridcolor="#E2E8F0"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # --- TABLEAU ---
    df_tab = df.copy()
    df_tab["Legendaire_Txt"] = df_tab["Legendaire"].map(lambda x: "★ Oui" if x else "Non")
    return kpi_count, kpi_total, kpi_record, kpi_pct_leg, fig_synthese, fig_scatter, df_tab.to_dict("records")


@app.callback(
    Output("duel-banniere", "children"),
    Output("graph-duel-radar", "figure"),
    Output("graph-duel-barres", "figure"),
    Input("store-pokedex", "data"),
    Input("duel-p1", "value"),
    Input("duel-p2", "value"),
)
def mettre_a_jour_duel(data, nom_p1, nom_p2):
    df = pd.DataFrame(data)
    r1 = df[df["Nom"] == nom_p1]
    r2 = df[df["Nom"] == nom_p2]
    if r1.empty or r2.empty:
        vide = _figure_vide("Sélectionnez deux Pokémon valides.")
        return "", vide, vide

    p1 = r1.iloc[0]
    p2 = r2.iloc[0]
    diff = int(p1["Total"] - p2["Total"])
    if diff > 0:
        verdict = f"Avantage {p1['Nom']} (+{diff} pts au Total)"
    elif diff < 0:
        verdict = f"Avantage {p2['Nom']} (+{abs(diff)} pts au Total)"
    else:
        verdict = "Égalité parfaite sur le Total !"

    banniere = html.Div(
        className="faceoff-banner d-flex justify-content-between align-items-center flex-wrap gap-3",
        children=[
            html.Div(
                [
                    html.Span(p1["Nom"], style={"color": "#FCA5A5", "fontWeight": "800", "fontSize": "1.1rem"}),
                    _badge_type_html(p1["Type1"]),
                    html.Div(f"Total : {int(p1['Total'])}", style={"fontSize": "0.85rem", "color": "#CBD5E1"}),
                ]
            ),
            html.Div([html.I(className="fa-solid fa-bolt me-2 text-warning"), verdict], className="fw-bold text-center"),
            html.Div(
                className="text-end",
                children=[
                    html.Span(p2["Nom"], style={"color": "#93C5FD", "fontWeight": "800", "fontSize": "1.1rem"}),
                    _badge_type_html(p2["Type1"]),
                    html.Div(f"Total : {int(p2['Total'])}", style={"fontSize": "0.85rem", "color": "#CBD5E1"}),
                ],
            ),
        ],
    )

    labels = [STATS_LABELS[c] for c in STATS_COLS]
    v1 = [int(p1[c]) for c in STATS_COLS]
    v2 = [int(p2[c]) for c in STATS_COLS]
    max_val = max(160, max(v1 + v2) + 15)

    # Radar Chart
    fig_radar = go.Figure()
    fig_radar.add_trace(
        go.Scatterpolar(
            r=v1 + [v1[0]], theta=labels + [labels[0]], fill="toself", name=p1["Nom"],
            fillcolor="rgba(220, 10, 45, 0.25)", line=dict(color="#DC0A2D", width=2.5),
        )
    )
    fig_radar.add_trace(
        go.Scatterpolar(
            r=v2 + [v2[0]], theta=labels + [labels[0]], fill="toself", name=p2["Nom"],
            fillcolor="rgba(42, 117, 187, 0.25)", line=dict(color="#2A75BB", width=2.5),
        )
    )
    fig_radar.update_layout(
        title=dict(text="Radar des 6 statistiques", font=dict(size=15)),
        polar=dict(radialaxis=dict(visible=True, range=[0, max_val])),
        legend=dict(orientation="h", y=-0.12),
        paper_bgcolor="rgba(0,0,0,0)",
    )

    # Barres comparatives
    fig_bar = go.Figure()
    fig_bar.add_trace(go.Bar(y=labels[::-1], x=v1[::-1], name=p1["Nom"], orientation="h", marker_color="#DC0A2D"))
    fig_bar.add_trace(go.Bar(y=labels[::-1], x=v2[::-1], name=p2["Nom"], orientation="h", marker_color="#2A75BB"))
    fig_bar.update_layout(
        title=dict(text="Comparaison stat par stat", font=dict(size=15)),
        barmode="group",
        xaxis_title="Valeur",
        legend=dict(orientation="h", y=-0.12),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )

    return banniere, fig_radar, fig_bar


if __name__ == "__main__":
    app.run(debug=True)