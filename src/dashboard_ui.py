"""Streamlit UI components for exploring the CITES trade network.

This module defines the DashboardUI class, which wires together a data
manager and graph builder to provide an interactive dashboard for
filtering CITES trade data and visualizing trade networks and maps.
"""
import pandas as pd
import streamlit as st


class DashboardUI:
    """High-level UI controller for the CITES trade dashboard.
    The DashboardUI coordinates data access through a data_manager and
    visualization through a graph_builder to render headers, filters,
    summary metrics, network graphs, and geographic maps in Streamlit.
    """


    def __init__(self, data_manager, graph_builder):
        """Initialize the dashboard with data and graph dependencies.

        Parameters
        ----------
        data_manager :
            Object providing access to CITES trade data and summary
            statistics (e.g., summary_stats, unique_taxa, filtering
            helpers).
        graph_builder :
            Object responsible for constructing network and map
            visualizations from filtered trade data.
        """

        self.data_manager = data_manager
        self.graph_builder = graph_builder

    def display_header(self):
        """Render the page configuration and static header content.

        Sets the Streamlit page layout, title, and descriptive markdown
        explaining the CITES trade database and providing reference links.
        """

        st.set_page_config(layout="wide")
        st.title("CITES Trade Network")
        st.markdown(
            """
        Full CITES Trade Database Download. Version [2022.1].
        Compiled by UNEP-WCMC, Cambridge, UK for the CITES Secretariat, Geneva, Switzerland.
        Available at: [https://trade.cites.org](https://trade.cites.org)
        """
        )
        st.markdown(
            """
        List of Contracting Parties with ISO codes - [https://cites.org/eng/disc/parties/chronolo.php](https://cites.org/eng/disc/parties/chronolo.php)
        """
        )

    def show_metrics(self):
        """Display high-level summary metrics for the trade dataset.

        Retrieves overall record, taxa, exporter, and importer counts
        from the data_manager and renders them as a small summary table
        in the Streamlit app.
        """

        metrics = self.data_manager.summary_stats()
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
            },
            index=[""],
        )
        st.table(summary_table, border="horizontal")

    def controls(self, itis):
        """Render taxon and trade filters and return the current selection.

        Provides controls for:
        - Choosing scientific vs common name search using a checkbox.
        - Selecting a focal taxon via a selectbox populated from merged
          trade taxa and ITIS metadata.
        - Selecting a year range for trade data via a slider.
        - Selecting a CITES term or choosing ALL terms.

        Parameters
        ----------
        itis : pandas.DataFrame
            ITIS taxonomic reference data with at least `complete_name`
            and `vernacular_name` columns for joining to the trade taxa.

        Returns
        -------
        taxon : str
            Selected scientific name (ITIS complete_name) for filtering.
        year_range : tuple[int, int]
            Inclusive range of trade years chosen in the slider.
        term : str or None
            Selected CITES term, or None if all terms should be included.
        """

        taxa_df = self.data_manager.unique_taxa()
        taxa_full = taxa_df.merge(itis, left_on="Taxon", right_on="complete_name")
        sci_check = st.checkbox("Scientific Name Search")
        if sci_check:
            taxon_select = st.selectbox(
                "Select Taxon - Scientific Name",
                sorted(taxa_full["complete_name"].unique()),
            )
            taxon_list = taxa_full[taxa_full["Taxon"] == taxon_select]
        else:
            taxon_select = st.selectbox(
                "Select Taxon - Common Name",
                sorted(taxa_full["vernacular_name"].unique()),
            )
            taxon_list = taxa_full[taxa_full["vernacular_name"] == taxon_select]
        taxon = taxon_list["complete_name"].values[0]
        year_range = st.slider("Select Trade Years", 1974, 2025, (1975, 2024))

        terms_df = self.data_manager.get_terms_for_taxon(taxon, year_range)
        term_options = ["ALL"] + sorted(terms_df["Term"].unique())
        term = st.selectbox("Select Term", term_options)
        purpose_df = self.data_manager.get_purpose_for_taxon(taxon, year_range, term)
        purpose_df = purpose_df[purpose_df["Purpose"].notna()]
        purpose_map = {
            "B": "Breeding in captivity or artificial propagation",
            "E": "Educational",
            "G": "Botanical garden",
            "H": "Hunting trophy",
            "L": "Law enforcement/judicial/forensic",
            "M": "Medical (including biomedical research)",
            "N": "Reintroduction or introduction into the wild",
            "P": "Personal",
            "Q": "Circus or travelling exhibition",
            "S": "Scientific",
            "T": "Commercial",
            "Z": "Zoo",
        }
        inverse_purpose_map = {v: k for k, v in purpose_map.items()}
        purpose_df["Purposes"] = purpose_df["Purpose"].map(purpose_map)
        purpose_options = ["ALL"] + sorted(purpose_df["Purposes"].unique())
        purpose_choice = st.selectbox("Select Purpose", purpose_options)


        if term == "ALL":
            term = None

        if purpose_choice == "ALL":
            purpose = None
        else:
            purpose = inverse_purpose_map.get(purpose_choice)

        return taxon, year_range, term, purpose

    def show_results(self, taxon, year_range, term):
        """Filter data based on selections and show a results summary.

        Filters the trade dataset using the selected taxon, year range,
        and term, then displays either a brief heading for the results
        section or a message prompting the user to expand the filters.
        """

        filtered_data = self.data_manager.filter_by_taxon(taxon, year_range, term, purpose)

        if not filtered_data.empty:
            st.write("Trade Weights by Countries")
        else:
            st.write("No results, please try again.")

    def graph_options(self, filtered_data, countries):
        """Provide controls for selecting exporter/importer and graph options.

        Merges filtered trade data with country metadata, then renders
        Streamlit widgets to choose an exporter, importer, edge weighting,
        and centrality scaling method for the network graph.

        Parameters
        ----------
        filtered_data : pandas.DataFrame
            Filtered trade records including exporter and importer codes.
        countries : pandas.DataFrame
            Country metadata with `country` and `name` columns used to
            map country codes to human-readable names.

        Returns
        -------
        exporter : str
            Selected exporter country code used for graph highlighting.
        importer : str
            Selected importer country code used for graph highlighting.
        weighted : bool
            Whether graph edges should be weighted by trade quantity.
        centrality_method : str
            Selected centrality label (e.g. "Degree", "Betweenness") to
            control node scaling in the network graph.
        """

        merged_exp = filtered_data.merge(
            countries, left_on="Exporter", right_on="country"
        )
        merged_imp = filtered_data.merge(
            countries, left_on="Importer", right_on="country"
        )
        exporters = merged_exp["name"].unique()
        exporter_sel = st.selectbox("Select :blue[Exporter]", sorted(exporters))
        if exporter_sel:
            merged_imp = merged_imp.loc[merged_imp["name"] != exporter_sel]
            importers = merged_imp["name"].unique()
            importer_sel = st.selectbox("Select :red[Importer]", sorted(importers))
        exporter = merged_exp.loc[merged_exp["name"] == exporter_sel, "country"].values[
            0
        ]
        importer = merged_imp.loc[merged_imp["name"] == importer_sel, "country"].values[
            0
        ]

        weighted = st.checkbox("Weighted Edges by Quantity of Trades")
        centrality_method = st.radio(
            "Scale Nodes by Centrality Measures",
            ["Degree", "In-Degree", "Out-Degree", "Betweenness", "Closeness"],
        )
        return exporter, importer, weighted, centrality_method

    def render_graph(
        self, exporter, importer, weighted, centrality_method
    ):
        """Build and style the trade network graph in the graph builder.

        Constructs a network graph from the filtered_data using the
        graph_builder, applies node scaling based on the chosen centrality
        metric, and colors exporter and importer nodes for emphasis.
        """
        graph = self.graph_builder.build_graph(weighted=weighted)
        self.graph_builder.scale_nodes(
            centrality_method.lower().replace("-", "").replace(" ", "")
        )
        self.graph_builder.color_nodes([exporter], [importer])

    def render_map(self, countries, exporter, importer):
        """Render a map of trade relationships in Streamlit.

        Uses the graph_builder to construct a Plotly map of trade between
        the selected exporter and importer countries and displays it with
        st.plotly_chart.
        """
        map_graph = self.graph_builder.build_map(countries, exporter, importer)
        st.plotly_chart(map_graph, width='stretch')
