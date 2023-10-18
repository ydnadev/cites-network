""" CITES trade network interactive Streamlit powered dashboard. """

import duckdb as dk
import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

st.set_page_config(layout="wide")
# Set header title
st.title("CITES Trade network")
st.markdown(
    """Full CITES Trade Database Download. Version [2022.1]. Compiled by UNEP-WCMC, Cambridge, UK
    for the CITES Secretariat, Geneva, Switzerland. Available at: [https://trade.cites.org]"""
)
st.markdown(
    """List of Contracting Parties with ISO codes -
    [https://cites.org/eng/disc/parties/chronolo.php]"""
)

# Read dataset (CSV)
tax = dk.query(" select distinct c.Taxon from 'data/cites_data.parquet' c ").df()

# Summary data
sm_taxon = dk.query(
    " select count(distinct c.Taxon) as taxon from 'data/cites_data.parquet' c "
).df()
sm_import = dk.query(
    " select count(distinct c.Importer) as importer from 'data/cites_data.parquet' c "
).df()
sm_export = dk.query(
    " select count(distinct c.Exporter) as exporter from 'data/cites_data.parquet' c "
).df()
sm_max_spp = dk.query(
    " select count(distinct c.Exporter) as exporter from 'data/cites_data.parquet' c "
).df()
taxon_num = sm_taxon["taxon"].values[0].astype(str)
import_num = sm_import["importer"].values[0].astype(str)
export_num = sm_export["exporter"].values[0].astype(str)
colA, colB, colC = st.columns(3)
colA.metric(label="Taxa ♞", value=taxon_num)
colB.metric(label="Exporters →", value=export_num)
colC.metric(label="Importers ←", value=import_num)

sp_filter = st.selectbox("Select/Type the Taxon", pd.unique(tax["Taxon"].sort_values()))

if sp_filter:
    # Filter for year of trade
    term_check = st.checkbox("Select Term")
    yrs = st.slider("Select Trade Years", 1974, 2023, (1975, 2022))
    if term_check:
        term_query = (
            "select distinct c.Term from 'data/cites_data.parquet' c where c.Taxon = '"
            + sp_filter
            + "' and c.Year >= '"
            + str(yrs[0])
            + "' and c.Year <= '"
            + str(yrs[1])
            + "'"
        )
        term = dk.query(term_query).df()
        if term.empty:
            # REGISTER to track whether term query is empty
            REGISTER = 0
        else:
            term_filter = st.selectbox(
                "Select/Type the Term", pd.unique(term["Term"].sort_values())
            )
            query = (
                """select c.Exporter as exporter
                ,c.export_ctry
                ,c.Importer as importer
                ,c.import_ctry
                ,sum(c.Quantity) as weight
                from 'data/cites_data.parquet' c
                where c.Taxon = '"""
                + sp_filter
                + "' and c.Year >= '"
                + str(yrs[0])
                + "' and c.Year <= '"
                + str(yrs[1])
                + "' and c.Term = '"
                + term_filter
                + "' group by c.Exporter, c.export_ctry, c.Importer, c.import_ctry"
            )
            query_full = (
                "select * from 'data/cites_data.parquet' c where c.Taxon = '"
                + sp_filter
                + "' and c.Year >= '"
                + str(yrs[0])
                + "' and c.Year <= '"
                + str(yrs[1])
                + "' and c.Term = '"
                + term_filter
                + "'"
            )
            REGISTER = 1
    else:
        query = (
            """select c.Exporter as exporter
            ,c.export_ctry
            ,c.Importer as importer
            ,c.import_ctry
            ,sum(c.Quantity) as weight
            from 'data/cites_data.parquet' c
            where c.Taxon = '"""
            + sp_filter
            + "' and c.Year >= '"
            + str(yrs[0])
            + "' and c.Year <= '"
            + str(yrs[1])
            + "' group by c.Exporter, c.export_ctry, c.Importer, c.import_ctry"
        )
        query_full = (
            "select * from 'data/cites_data.parquet' c where c.Taxon = '"
            + sp_filter
            + "' and c.Year >= '"
            + str(yrs[0])
            + "' and c.Year <= '"
            + str(yrs[1])
            + "'"
        )
        REGISTER = 1
    # Query data
    if REGISTER == 0:
        data = pd.DataFrame()
    else:
        data = dk.query(query).df()
    if data.empty:
        st.write("No results, please expand years.")
    else:
        num_results = len(data.index)
        RES_STMNT = "Results returned: " + str(num_results)
        st.write(RES_STMNT)
        if num_results < 1000:
            full_data = dk.query(query_full).df()
            full_data["Id"] = full_data["Id"].astype(str)
            full_data["Year"] = full_data["Year"].astype(str)

            # Select Importer and Exporter colors
            ex_filter = st.selectbox(
                "Select/Type the :orange[Exporter]",
                pd.unique(data["export_ctry"].sort_values()),
            )
            im_filter = st.selectbox(
                "Select/Type the :red[Importer]",
                pd.unique(data["import_ctry"].sort_values()),
            )

            # Weighted edges
            weighted = st.checkbox("Weighted Edges by Quantity of Trades")
            if weighted:
                species = nx.from_pandas_edgelist(
                    data,
                    source="export_ctry",
                    target="import_ctry",
                    edge_attr="weight",
                    create_using=nx.DiGraph(),
                )
                #print(species.edge_attr)
            else:
                species = nx.from_pandas_edgelist(
                    data,
                    source="export_ctry",
                    target="import_ctry",
                    create_using=nx.DiGraph(),
                )
            
            # Node Centrality
            dgree = st.checkbox("Scale Nodes by Number of Trading Partners", value=True)
            if dgree:
                centrality = st.radio(
                        "Scale Nodes by Centrality Measures",
                        ["Degree (connections)",
                            "In-Degree (incoming connections)",
                            "Out-Degree (outgoing connections)",
                            #"Eigenvector (centrality of neighbors)",
                            "Closeness (distance to other nodes)",
                            "Betweenness (frequency as shortest path)"])
                       # captions = ["number of edges",
                       #     "centrality of neighbors",
                       #     "shortest path to other nodes"])
            
                # Adding scaling for node size
                if centrality == "Degree (connections)":
                    cent = nx.degree_centrality(species)
                    cent.update((x, 100 * y) for x, y in cent.items())
                    nx.set_node_attributes(species, cent, "size")
                elif centrality == "In-Degree (incoming connections)":
                    cent = nx.in_degree_centrality(species)
                    cent.update((x, 100 * y) for x, y in cent.items())
                    nx.set_node_attributes(species, cent, "size")
                elif centrality == "Out-Degree (outgoing connections)":
                    cent = nx.out_degree_centrality(species)
                    cent.update((x, 100 * y) for x, y in cent.items())
                    nx.set_node_attributes(species, cent, "size")
                elif centrality == "Eigenvector (centrality of neighbors)":
                    cent = nx.eigenvector_centrality(species)
                    cent.update((x, 100 * y) for x, y in cent.items())
                    nx.set_node_attributes(species, cent, "size")
                elif centrality == "Closeness (shortest path to other nodes)":
                    cent = nx.closeness_centrality(species)
                    cent.update((x, 100 * y) for x, y in cent.items())
                    nx.set_node_attributes(species, cent, "size")
                elif centrality == "Betweenness (frequency as shortest path)":
                    cent = nx.betweenness_centrality(species)
                    cent.update((x, 100 * y) for x, y in cent.items())
                    nx.set_node_attributes(species, cent, "size")


            # Take Networkx graph and translate it to a PyVis graph format
            anim_net = Network(
                height="900px", bgcolor="white", font_color="blue", directed=True
            )
            anim_net.from_nx(species)

            # Color based on import/export
            for node in anim_net.nodes:
                if node["id"] == ex_filter:
                    node["color"] = "orange"
                elif node["id"] == im_filter:
                    node["color"] = "red"
                else:
                    node["color"] = "grey"

            # Generate network with specific layout settings
            anim_net.repulsion(
                node_distance=420,
                central_gravity=0.33,
                spring_length=110,
                spring_strength=0.10,
                damping=0.95,
            )

            # Save and read graph as HTML file (on Streamlit Sharing)
            try:
                PATH = "/tmp"
                anim_net.save_graph(f"{PATH}/pyvis_graph.html")
                HtmlFile = open(f"{PATH}/pyvis_graph.html", "r", encoding="utf-8")

            # Save and read graph as HTML file (locally)
            except OSError:
                PATH = "html_files"
                anim_net.save_graph(f"{PATH}/pyvis_graph.html")
                HtmlFile = open(f"{PATH}/pyvis_graph.html", "r", encoding="utf-8")

            # Load HTML file in HTML component for display on Streamlit page
            components.html(HtmlFile.read(), height=1500, width=1500)
            HtmlFile.close()

            st.dataframe(data)
            st.dataframe(full_data.set_index(full_data.columns[0]))

        else:
            st.write("Too many nodes to plot, please narrow search.")

st.markdown("[https://github.com/ydnadev/cites-network]")
