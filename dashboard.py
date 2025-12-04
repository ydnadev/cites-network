import streamlit as st
from src.data_manager import CITESDataManager
from src.network_graph import NetworkGraphBuilder
from src.dashboard_ui import DashboardUI


def main():
    # Paths to your data files
    parquet_path = "data/cites_data.parquet"
    countries_csv = "data/countries.csv"
    itis_csv = "data/itis_vernacular.csv"

    # Initialize class instances
    data_manager = CITESDataManager(parquet_path, countries_csv, itis_csv)
    countries = data_manager.countries
    itis = data_manager.itis
    graph_builder = NetworkGraphBuilder(
        data=None, countries=countries
    )  # data will be set after filtering
    dashboard = DashboardUI(data_manager, graph_builder)

    # Render dashboard sections
    dashboard.display_header()
    dashboard.show_metrics()

    # Main UI controls and results loop
    col1, col2 = st.columns(2)
    with col1:
        taxon, year_range, term, purpose, source = dashboard.controls(itis)
        filtered_data = data_manager.filter_by_taxon(taxon, year_range, term, purpose, source)
        filtered_results = data_manager.filter_by_taxon_results(taxon, year_range, term, purpose, source)
        if not filtered_data.empty:
            graph_builder.data = filtered_data
            exporter_sel, importer_sel, weighted, centrality_method = (
                dashboard.graph_options(filtered_data, countries)
            )

            # Graph visualization
            with col2:
                dashboard.render_graph(
                    exporter_sel, importer_sel, weighted, centrality_method
                )
                dashboard.render_map(countries, exporter_sel, importer_sel)
                st.markdown("*Note - Map generated with Exporter reported data to avoid duplication.*")
                st.dataframe(filtered_results, hide_index=True)

        else:
            st.markdown(":red[*No results, please try again.*]")

if __name__ == "__main__":
    main()
