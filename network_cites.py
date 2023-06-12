import duckdb as dk 
import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

# Read dataset (CSV)
#df = pd.read_csv('network_data.csv')
tax = dk.query(''' select distinct c.Taxon from 'data/cites_data.parquet' c ''').df()

# Set header title
st.title('CITES Trade network')
st.markdown('Full CITES Trade Database Download. Version [2022.1]. Compiled by UNEP-WCMC, Cambridge, UK for the CITES Secretariat, Geneva, Switzerland. Available at: [https://trade.cites.org]')
st.markdown('List of Contracting Parties with ISO codes - [https://cites.org/eng/disc/parties/chronolo.php]')

sp_filter = st.selectbox("Select/Type the Taxon", pd.unique(tax["Taxon"].sort_values()))

if sp_filter:
   
    # Filter for year of trade
    yr_check = st.checkbox('Select Year')
    if yr_check:
        yr_query = "select distinct c.Year from 'data/cites_data.parquet' c where c.Taxon = " + "'" + sp_filter + "'"
        yr = dk.query(yr_query).df()
        yr_filter = st.selectbox("Select/Type the Year", pd.unique(yr["Year"].sort_values()))
        query = "select c.Importer as importer, c.Exporter as exporter, count(*) as weight from 'data/cites_data.parquet' c where c.Taxon = "
        query_stmn = query + "'" + sp_filter + "' and c.Year = '" + yr_filter.astype(str) + "' group by c.Importer, c.Exporter"
    else: 
        query = "select c.Importer as importer, c.Exporter as exporter, count(*) as weight from 'data/cites_data.parquet' c where c.Taxon = "
        query_stmn = query + "'" + sp_filter + "' group by c.Importer, c.Exporter"

    # Query data 
    df2 = dk.query(query_stmn).df()

    # Select Importer and Exporter colors
    ex_filter = st.selectbox("Select/Type the :orange[Exporter]", pd.unique(df2["exporter"].sort_values()))
    im_filter = st.selectbox("Select/Type the :red[Importer]", pd.unique(df2["importer"].sort_values()))

    # Select if directed or weighted and Initiated PyViz graph
    directed = st.checkbox('Directed')
    weighted = st.checkbox('Weighted by trades')
    if weighted:
        species = nx.from_pandas_edgelist(df2, 'exporter', 'importer', 'weight')
    else:
        species = nx.from_pandas_edgelist(df2, 'exporter', 'importer')
    if directed:
        anim_net = Network(height='1000px', bgcolor='white', font_color='blue', directed=True)
    else:
        anim_net = Network(height='1000px', bgcolor='white', font_color='blue')

    # Take Networkx graph and translate it to a PyVis graph format
    anim_net.from_nx(species)

    # Color based on import/export
    for node in anim_net.nodes:
        if node['id'] == ex_filter:
            node['color'] = 'orange'
        elif node['id'] == im_filter:
            node['color'] = 'red'
        else:
            node['color'] = 'grey'

    # Generate network with specific layout settings
    anim_net.repulsion(node_distance=420, central_gravity=0.33,
                       spring_length=110, spring_strength=0.10,
                       damping=0.95)

    # Save and read graph as HTML file (on Streamlit Sharing)
    try:
        path = '/tmp'
        anim_net.save_graph(f'{path}/pyvis_graph.html')
        HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

    # Save and read graph as HTML file (locally)
    except:
        path = 'html_files'
        anim_net.save_graph(f'{path}/pyvis_graph.html')
        HtmlFile = open(f'{path}/pyvis_graph.html', 'r', encoding='utf-8')

    # Load HTML file in HTML component for display on Streamlit page
    components.html(HtmlFile.read(), height=1100)
    HtmlFile.close()

    st.dataframe(df2)

st.markdown('[https://github.com/ydnadev/cites-network]')
