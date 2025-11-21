import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

class DashboardUI:
    def __init__(self, data_manager, graph_builder):
        self.data_manager = data_manager
        self.graph_builder = graph_builder

    def display_header(self):
        st.set_page_config(layout="wide")
        st.title("CITES Trade Network")
        st.markdown("""
        Full CITES Trade Database Download. Version [2022.1].
        Compiled by UNEP-WCMC, Cambridge, UK for the CITES Secretariat, Geneva, Switzerland.
        Available at: [https://trade.cites.org](https://trade.cites.org)
        """)
        st.markdown("""
        List of Contracting Parties with ISO codes - [https://cites.org/eng/disc/parties/chronolo.php](https://cites.org/eng/disc/parties/chronolo.php)
        """)

    def show_metrics(self):
        metrics = self.data_manager.summary_stats()
        #colA, colB, colC, colD = st.columns(4)
        #colA.metric(label="Records", value=metrics["rows"])
        #colA.metric(label="Records", value=f"{metrics['rows']:,}")
        #colB.metric(label="Taxa", value=metrics["taxa"])
        #colC.metric(label="Exporters", value=metrics["exporters"])
        #colD.metric(label="Importers", value=metrics["importers"])

        rows = f"{metrics['rows']:,}"
        taxa = f"{metrics['taxa']:,}"
        exprts = f"{metrics['exporters']:,}"
        imprts = f"{metrics['importers']:,}"
        summary_table = pd.DataFrame(
            {
                "Records": rows,
                "Taxa": taxa,
                "Exporters": exprts,
                "Importers": imprts,
            } ,   index=[""],
        )
        st.table(summary_table, border="horizontal")

    def controls(self, itis):
        taxa_df = self.data_manager.unique_taxa()
        taxa_full = taxa_df.merge(itis, left_on='Taxon', right_on='complete_name')
        taxon_common = st.selectbox("Select Taxon", sorted(taxa_full["vernacular_name"].unique()))
        taxon_list = taxa_full[taxa_full['vernacular_name'] == taxon_common]
        taxon = taxon_list["complete_name"].values[0]
        term_check = st.checkbox("Select Term")
        year_range = st.slider("Select Trade Years", 1974, 2023, (1975, 2022))
        if term_check:
            terms_df = self.data_manager.get_terms_for_taxon(taxon, year_range)
            term = st.selectbox("Select Term", sorted(terms_df["Term"].unique()))
        else:
            term = None
        return taxon, year_range, term

    def show_results(self, taxon, year_range, term):
        filtered_data = self.data_manager.filter_by_taxon(taxon, year_range, term)

        if not filtered_data.empty:
            st.write("Trade Weights by Countries")
        else:
            st.write("No results, please expand years.")

    def graph_options(self, filtered_data, countries):
        merged_exp = filtered_data.merge(countries, left_on='Exporter', right_on='country')
        merged_imp = filtered_data.merge(countries, left_on='Importer', right_on='country')
        #exporters = filtered_data["export_ctry"].unique()
        #importers = filtered_data["import_ctry"].unique()
        exporters = merged_exp["name"].unique()
        exporter_sel = st.selectbox("Select :blue[Exporter]", sorted(exporters))
        if exporter_sel:
            merged_imp = merged_imp.loc[merged_imp['name'] != exporter_sel]
            importers = merged_imp["name"].unique()
            importer_sel = st.selectbox("Select :red[Importer]", sorted(importers))
        exporter = merged_exp.loc[merged_exp['name'] == exporter_sel, 'country'].values[0]
        #expt = ":blue[" + exporter_sel + "]"
        #impt = ":red[" + exporter_sel + "]"
        #cmb = expt + " " + impt
        #st.markdown(cmb)
        #st.dataframe(merged_imp)
        importer = merged_imp.loc[merged_imp['name'] == importer_sel, 'country'].values[0]

        weighted = st.checkbox("Weighted Edges by Quantity of Trades")
        centrality_method = st.radio(
            "Scale Nodes by Centrality Measures",
            ["Degree", "In-Degree", "Out-Degree", "Closeness", "Betweenness"]
        )
        return exporter, importer, weighted, centrality_method

    def render_graph(self, filtered_data, exporter, importer, weighted, centrality_method):
        graph = self.graph_builder.build_graph(weighted=weighted)
        self.graph_builder.scale_nodes(centrality_method.lower().replace("-", "").replace(" ", ""))
        self.graph_builder.color_nodes([exporter], [importer])
    #    net = self.graph_builder.to_pyvis()
        #net.show("display_graph.html")
        #HtmlFile = open("display_graph.html", "r", encoding="utf-8")
        #components.html(HtmlFile.read(), height=900, width=1500)

    def render_map(self, countries, exporter, importer):
        map_graph = self.graph_builder.build_map(countries, exporter, importer)
        st.plotly_chart(map_graph, use_container_width=True)
        #self.graph_builder.scale_nodes(centrality_method.lower().replace("-", "").replace(" ", ""))
        #self.graph_builder.color_nodes([exporter], [importer])

    #def display_columns(self, filtered_data, countries, exporter, importer, weighted, centrality_method):
    #    col1, col2 = st.columns(2)
    #    with col1:
    #        # Call your render_graph function and display the graph
    #        self.controls()
    #        # If graph output is returned as a component (e.g., via st.plotly_chart, st.components.v1.html, etc.), display here.

    #    with col2:
    #        # Call your render_map function and display the map
    #        self.render_map(countries, exporter, importer)