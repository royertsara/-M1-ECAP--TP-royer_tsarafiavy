import dash
from dash import html, dcc, dash_table, Input, Output
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import calendar

#-------Initialise APP
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

server = app.server


# -------------------------------- Data load -----------------------------------------------
df = pd.read_csv("data.csv", sep=",", encoding="utf-8")

# On garde les colonnes qui nous intéressent
df=df[['CustomerID', 'Gender', 'Location', 'Product_Category', 'Quantity', 'Avg_Price', 'Transaction_Date', 'Month', 'Discount_pct']]
# Conversion des colonnes critiques
df['CustomerID'] = pd.to_numeric(df['CustomerID'], errors='coerce')  # int
df['Transaction_Date'] = pd.to_datetime(df['Transaction_Date'], errors='coerce')  # datetime
df['Quantity'] = pd.to_numeric(df['Quantity'], errors='coerce')  # int
df['Avg_Price'] = pd.to_numeric(df['Avg_Price'], errors='coerce')  # float
df['Discount_pct'] = pd.to_numeric(df['Discount_pct'], errors='coerce')  # float
df['Month'] = pd.to_numeric(df['Month'], errors='coerce')

# Gestion des valeurs manquantes:
df.dropna(inplace=True)

# Colonnes dérivées
df['Total_prices'] = df['Avg_Price'] * (1 - df['Discount_pct']/100)
df['CA'] = df['Quantity'] * df['Total_prices']


# -------------------------------- Fonctions métiers-------------------------
def frequence_meilleurs_ventes(df):
    x = df.groupby(['Product_Category','Gender'])['Quantity'].sum().reset_index()
    return x.sort_values(by='Quantity', ascending=False).head(10)

def indicateur_mois(df, mois):
    mask = (df['Month'] == mois)
    mois_prec = 12 if mois == 1 else mois-1
    mask_prec = (df['Month'] == mois_prec)
    return {
        "mois": calendar.month_name[mois],
        "ventes": {
            "value": round(df.loc[mask,'Quantity'].sum(),2),
            "reference": round(df.loc[mask_prec,'Quantity'].sum(),2)
        },
        "ca": {
            "value": round(df.loc[mask,'CA'].sum(),2),
            "reference": round(df.loc[mask_prec,'CA'].sum(),2)
        }
    }

# -------------------------------- Dash App ---------------------------------------------

app.layout = dbc.Container(
    fluid=True,
    style={"height": "100vh", "padding": "0"},
    children=[

        # ---------------- HEADER ----------------
        dbc.Navbar(
            dbc.Container([
                html.H4("ECAP Store – Dashboard", className="text-light m-0"),
                dcc.Dropdown(
                    id="drop-1",
                    options=[{"label": i, "value": i} for i in df["Location"].unique()],
                    placeholder="Filtrer par localisation",
                    clearable=True,
                    style={"width": "250px"}
                )
            ]),
            color="primary",
            dark=True,
            style={"height": "8vh"}
        ),

        # ---------------- MAIN GRID ----------------
        dbc.Row(
            style={"height": "92vh"},
            className="g-2",
            children=[

                # ----------- COLONNE GAUCHE -----------
                dbc.Col(
                    width=5,
                    className="d-flex flex-column",
                    children=[

                        # KPI Row (hauteur fixe)
                        dbc.Row(
                            style={"height": "25vh"},
                            className="g-2",
                            children=[
                                dbc.Col(
                                    dcc.Graph(
                                        id="kpi-ca",
                                        config={"responsive": True},
                                        style={"width": "100%", "height": "100%"}
                                    )
                                ),
                                dbc.Col(
                                    dcc.Graph(
                                        id="kpi-ventes",
                                        config={"responsive": True},
                                        style={"width": "100%", "height": "100%"}
                                    )
                                ),
                            ]
                        ),

                        # Barplot (hauteur fixe)
                        dbc.Row(
                            style={"height": "65vh"},
                            children=[
                                dbc.Col(
                                    dcc.Graph(
                                        id="graph-top10",
                                        config={"responsive": True},
                                        style={"width": "100%", "height": "100%"}
                                    )
                                )
                            ]
                        )
                    ]
                ),

                # ----------- COLONNE DROITE -----------
                dbc.Col(
                    width=7,
                    className="d-flex flex-column",
                    children=[

                        # Line chart
                        dbc.Row(
                            style={"height": "45vh"},
                            children=[
                                dbc.Col(
                                    dcc.Graph(
                                        id="graph-evo",
                                        config={"responsive": True},
                                        style={"width": "100%", "height": "100%"}
                                    )
                                )
                            ]
                        ),

                        # Table
                        dbc.Row(
                            style={"height": "45vh"},
                            children=[
                            
                                dbc.Col(
                                    className="d-flex flex-column",
                                    children=[

                                # ---- Titre ----
                                    html.H5(
                                        "Top 100 Transactions",
                                                className="mb-2",
                                         style={"fontWeight": "bold"}
                                        ),

                                    dash_table.DataTable(
                                                         id="table-top100",
                                                        columns=[{"name": c, "id": c} for c in df[['Transaction_Date','Gender','Location','Product_Category','Quantity','Avg_Price','Discount_pct']].columns],

                                                        page_size=10,
                                                        sort_action="native",
                                                        filter_action="native",
                                                        column_selectable="multi",
                                                        style_table={
                                                            "flex": "1",
                                                            "overflowY": "auto",
                                                            "border": "1px solid #dee2e6",
                                                        },
                                                        style_header={
                                                            "backgroundColor": "#f8f9fa",
                                                            "fontWeight": "bold",
                                                            "borderBottom": "1px solid #dee2e6"
                                                        },
                                                        style_cell={
                                                            "padding": "6px",
                                                            "fontSize": "12px",
                                                            "whiteSpace": "normal",
                                                            "textAlign": "left",
                                                        }
                                                    )

                                ] 
                             
                             )
                            ]
                        )
                    ]
                )
            ]
        )
    ]
)

# ---------------- Callback  ----------------
@app.callback(
    Output("kpi-ca", "figure"),
    Output("kpi-ventes", "figure"),
    Output("graph-top10", "figure"),
    Output("graph-evo", "figure"),
    Output("table-top100", "data"),
    Input("drop-1", "value")
)
def update_dashboard(location):
    dff = df if location is None else df[df["Location"]==location]
    res = indicateur_mois(dff, 12)

    # Communs pour les graphiques pour éviter les marges énormes
    layout_args = dict(margin=dict(t=40, b=20, l=20, r=20))

    # KPI CA
    fig_kpi_ca = go.Figure(go.Indicator(
        mode="number+delta",
        value=res["ca"]["value"],
        delta={"reference": res["ca"]["reference"]},
        title={"text": res["mois"]}
    ))
    fig_kpi_ca.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200)

    # KPI Ventes
    fig_kpi_ventes = go.Figure(go.Indicator(
        mode="number+delta",
        value=res["ventes"]["value"],
        delta={"reference": res["ventes"]["reference"]},
        title={"text":res['mois']}
    ))
    fig_kpi_ventes.update_layout(margin=dict(t=0, b=0, l=0, r=0), height=200)

    # Barplot
    data_top10 = frequence_meilleurs_ventes(dff)
    fig_top10 = px.bar(data_top10, x="Quantity", y="Product_Category", color="Gender", 
                       barmode="group", title="Top 10 Ventes",labels={"Quantity":"Quantité Totale","Product_Category":"Catégories"})
    fig_top10.update_layout(**layout_args)

    # Line Chart
    evo_ca = dff.groupby(pd.Grouper(key='Transaction_Date', freq='W'))['CA'].sum().reset_index()
    fig_evo = px.line(evo_ca, x="Transaction_Date", y="CA", title="Evolution du Chiffres d'affaires par semaine",labels={
        "Transaction_Date": "Semaine",
        "CA": "Chiffre d'affaires "
        }
    )
    fig_evo.update_layout(**layout_args)

    # Table
    top100 = dff[['Transaction_Date','Gender','Location','Product_Category','Quantity','Avg_Price','Discount_pct']]
    table_data = top100.sort_values(by='Transaction_Date', ascending=False).head(100).to_dict("records")

    return fig_kpi_ca, fig_kpi_ventes, fig_top10, fig_evo, table_data

if __name__ == "__main__":
    app.run_server(debug=True)