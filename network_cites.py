import duckdb as dk 
import networkx as nx
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from pyvis.network import Network

# Set header title
st.title('CITES Trade network')
st.markdown('Full CITES Trade Database Download. Version [2022.1]. Compiled by UNEP-WCMC, Cambridge, UK for the CITES Secretariat, Geneva, Switzerland. Available at: [https://trade.cites.org]')
st.markdown('List of Contracting Parties with ISO codes - [https://cites.org/eng/disc/parties/chronolo.php]')

# Read dataset (CSV)
tax = dk.query(" select distinct c.Taxon from 'data/cites_data.parquet' c ").df()

# Summary data 
sm_taxon = dk.query(" select count(distinct c.Taxon) as taxon from 'data/cites_data.parquet' c ").df()
sm_import = dk.query(" select count(distinct c.Importer) as importer from 'data/cites_data.parquet' c ").df()
sm_export = dk.query(" select count(distinct c.Exporter) as exporter from 'data/cites_data.parquet' c ").df()
sm_max_spp = dk.query(" select count(distinct c.Exporter) as exporter from 'data/cites_data.parquet' c ").df()
taxon_num = sm_taxon['taxon'].values[0].astype(str)
import_num = sm_import['importer'].values[0].astype(str)
export_num = sm_export['exporter'].values[0].astype(str)
colA, colB, colC = st.columns(3)
colA.metric(
    label='Taxon ♞',
    value=taxon_num
)
colB.metric(
    label='Exporters →',
    value=export_num
)
colC.metric(
    label='Importers ←',
    value=import_num
)

sp_filter = st.selectbox("Select/Type the Taxon", pd.unique(tax["Taxon"].sort_values()))

if sp_filter:
   
    # Filter for year of trade
    yr_check = st.checkbox('Select Year')
    term_check = st.checkbox('Select Term')
    if yr_check:
        yr_query = "select distinct c.Year from 'data/cites_data.parquet' c where c.Taxon = " + "'" + sp_filter + "'"
        yr = dk.query(yr_query).df()
        yr_filter = st.selectbox("Select/Type the Year", pd.unique(yr["Year"].sort_values()))
        if term_check:
            term_query = "select distinct c.Term from 'data/cites_data.parquet' c where c.Taxon = " + "'" + sp_filter + "' and c.Year = '" + yr_filter.astype(str) + "'" 
            term = dk.query(term_query).df()
            term_filter = st.selectbox("Select/Type the Term", pd.unique(term["Term"].sort_values()))
            query = "select c.Importer as importer, c.Exporter as exporter, sum(c.Quantity) as weight from 'data/cites_data.parquet' c where c.Taxon = "
            query_stmn = query + "'" + sp_filter + "' and c.Year = '" + yr_filter.astype(str) + "' and c.Term = '" + term_filter + "' group by c.Importer, c.Exporter"
            query_full = "select * from 'data/cites_data.parquet' c where c.Taxon = "
            query_full_stmn = query_full + "'" + sp_filter + "' and c.Year = '" + yr_filter.astype(str) + "' and c.Term = '" + term_filter + "'"
        else:
            query = "select c.Importer as importer, c.Exporter as exporter, sum(c.Quantity) as weight from 'data/cites_data.parquet' c where c.Taxon = "
            query_stmn = query + "'" + sp_filter + "' and c.Year = '" + yr_filter.astype(str) + "' group by c.Importer, c.Exporter"
            query_full = "select * from 'data/cites_data.parquet' c where c.Taxon = "
            query_full_stmn = query_full + "'" + sp_filter + "' and c.Year = '" + yr_filter.astype(str) + "'"
    else: 
        if term_check:
            term_query = "select distinct c.Term from 'data/cites_data.parquet' c where c.Taxon = " + "'" + sp_filter + "'" 
            term = dk.query(term_query).df()
            term_filter = st.selectbox("Select/Type the Term", pd.unique(term["Term"].sort_values()))
            query = "select c.Importer as importer, c.Exporter as exporter, sum(c.Quantity) as weight from 'data/cites_data.parquet' c where c.Taxon = "
            query_stmn = query + "'" + sp_filter + "' and c.Term = '" + term_filter + "' group by c.Importer, c.Exporter"
            query_full = "select * from 'data/cites_data.parquet' c where c.Taxon = "
            query_full_stmn = query_full + "'" + sp_filter + "' and c.Term = '" + term_filter + "'"
        else:
            query = "select c.Importer as importer, c.Exporter as exporter, sum(c.Quantity) as weight from 'data/cites_data.parquet' c where c.Taxon = "
            query_stmn = query + "'" + sp_filter + "' group by c.Importer, c.Exporter"
            query_full = "select * from 'data/cites_data.parquet' c where c.Taxon = "
            query_full_stmn = query_full + "'" + sp_filter + "'"

    # Query data 
    data = dk.query(query_stmn).df()
    full_data = dk.query(query_full_stmn).df()
    full_data['Id'] = full_data['Id'].astype(str)
    full_data['Year'] = full_data['Year'].astype(str)


    # Select Importer and Exporter colors
    ex_filter = st.selectbox("Select/Type the :orange[Exporter]", pd.unique(data["exporter"].sort_values()))
    im_filter = st.selectbox("Select/Type the :red[Importer]", pd.unique(data["importer"].sort_values()))

    # Select if directed or weighted and Initiated PyViz graph
    directed = st.checkbox('Directed')
    weighted = st.checkbox('Weighted by trades')
    if weighted:
        species = nx.from_pandas_edgelist(data, 'exporter', 'importer', 'weight')
    else:
        species = nx.from_pandas_edgelist(data, 'exporter', 'importer')
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

    st.dataframe(data)
    st.dataframe(full_data.set_index(full_data.columns[0]))

st.markdown('[https://github.com/ydnadev/cites-network]')
