"""
Network graph visualization utilities for trade and connectivity analysis.

This module renders directed graphs from trade data between countries.
It uses NetworkX for graph construction and supports node scaling by
centrality measures.

Key components:
- NetworkGraphBuilder: Main class for creating and customizing graphs.

Dependencies:
- networkx: Graph creation and analysis.
- streamlit: Web app integration (optional).
- plotly: Geographic map rendering.
- pyvis: Interactive network visualization.

Example usage:
    builder = NetworkGraphBuilder(data_df, countries_df)
    graph = builder.build_graph(weighted=True)
    builder.scale_nodes("betweenness")
    builder.color_nodes(exporters_set, importers_set)
    map_fig = builder.build_map(countries_df, "USA", "CHN")
    map_fig.show()
"""
import networkx as nx
import plotly.graph_objects as go
from pyvis.network import Network


class NetworkGraphBuilder:
    """Build and visualize directed trade networks on map.

    This class constructs a directed NetworkX graph from an edge list of cites trades,
    scales and colors nodes using various centrality measures and exporter/importer
    roles, and provides helpers to render the result as a PyVis network or a
    Plotly geographic map.
    """
    def __init__(
        self,
        data,
        countries,
        exporter_color="#1f77b4",
        importer_color="#ff7f0e",
        default_color="rgb(0,0,0)",
    ):
        """Initialize the network graph builder.

        Args:
            data: Pandas DataFrame with exporter, importer, and optional weight columns.
            countries: DataFrame with country identifiers and geographic metadata.
            exporter_color: Color used to highlight exporter nodes.
            importer_color: Color used to highlight importer nodes.
            default_color: Color used for non-highlighted nodes.
        """
        self.data = (
            data  # DataFrame with columns for exporters, importers, quantity, countries
        )
        self.countries = countries
        self.exporter_color = exporter_color
        self.importer_color = importer_color
        self.default_color = default_color
        self.graph = None
        self.map = None

    def build_graph(self, weighted=False):
        """Build a directed NetworkX graph from the edge list.

        Args:
            weighted: If True, use the 'Weight' column as an edge attribute.

        Returns:
            The constructed directed NetworkX graph.
        """
        if weighted:
            self.graph = nx.from_pandas_edgelist(
                self.data,
                source="Exporter",
                target="Importer",
                edge_attr="Weight",
                create_using=nx.DiGraph(),
            )
        else:
            self.graph = nx.from_pandas_edgelist(
                self.data,
                source="Exporter",
                target="Importer",
                create_using=nx.DiGraph(),
            )
        return self.graph

    def scale_nodes(self, scale_method="degree"):
        """Set node sizes based on a centrality measure.

        Args:
            scale_method: Centrality metric name, such as 'degree', 'indegree',
                'outdegree', 'eigenvector', 'closeness', or 'betweenness'.

        Returns:
            The graph with a 'size' node attribute applied.
        """
        if not self.graph:
            raise ValueError("Graph not built.")
        centrality_methods = {
            "degree": nx.degree_centrality,
            "indegree": nx.in_degree_centrality,
            "outdegree": nx.out_degree_centrality,
            "eigenvector": nx.eigenvector_centrality,
            "closeness": nx.closeness_centrality,
            "betweenness": nx.betweenness_centrality,
        }
        if scale_method in centrality_methods:
            cent = centrality_methods[scale_method](self.graph)
            for node, value in cent.items():
                nx.set_node_attributes(self.graph, {node: value * 100}, "size")
        return self.graph

    def color_nodes(self, exporters, importers):
        """Color nodes based on exporter/importer role.

        Args:
            exporters: Iterable of node identifiers treated as exporters.
            importers: Iterable of node identifiers treated as importers.

        Returns:
            The graph with a 'color' node attribute applied.
        """
        color_attr = {}
        for node in self.graph.nodes:
            if node in exporters:
                color_attr[node] = self.exporter_color
            elif node in importers:
                color_attr[node] = self.importer_color
            else:
                color_attr[node] = self.default_color
        nx.set_node_attributes(self.graph, color_attr, "color")
        return self.graph

    def to_pyvis(self, height="900px", directed=True):
        """Convert the NetworkX graph to a PyVis Network object.

        Args:
            height: Height of the rendered PyVis canvas.
            directed: Whether to treat the graph as directed in the visualization.

        Returns:
            A configured PyVis Network instance.
        """
        net = Network(height=height, directed=directed)
        net.from_nx(self.graph)
        net.repulsion(
            node_distance=420,
            central_gravity=0.33,
            spring_length=110,
            spring_strength=0.1,
            damping=0.95,
        )
        return net

    def build_map(self, countries, exporter_sel, importer_sel):
        """Build a Plotly map for the network.

        Nodes are positioned by country coordinates and edges are colored to
        highlight a selected exporter–importer pair.

        Args:
            countries: DataFrame with 'country', 'longitude', 'latitude', and 'name'.
            exporter_sel: Node identifier to highlight as the exporter.
            importer_sel: Node identifier to highlight as the importer.

        Returns:
            A Plotly Figure object showing the network on a world map.
        """
        # Map country code to coordinates and names
        ex_code = exporter_sel
        im_code = importer_sel
        node_pos = {}
        for node in self.graph.nodes():
            match = countries.loc[countries["country"] == node]
            if not match.empty:
                row = match.iloc[0]
                node_pos[node] = (row["longitude"], row["latitude"])
            else:
                node_pos[node] = (0, 0)
        node_names = []
        for node in self.graph.nodes():
            match = countries.loc[countries["country"] == node, "name"]
            node_names.append(match.values[0] if not match.empty else "XX")

        # Adjust node sizes
        node_sizes = [
            self.graph.nodes[node].get("size", 8) for node in self.graph.nodes()
        ]
        node_colors = [
            self.graph.nodes[node].get("color", "grey") for node in self.graph.nodes()
        ]

        # Build edge traces for the network
        edge_traces = []
        for src, dst in self.graph.edges():
            if src == ex_code and dst == im_code:
                # COLOR EDGE PURPLE IF TRADE FROM EXPORTER TO IMPORTER SELECTIONS
                edge_color = "#9467bd"
            elif src == ex_code:
                # COLOR EDGE BLUE FOR EXPORTS FROM EXPORTER SELECTION
                edge_color = "#1f77b4"
            elif dst == im_code:
                # COLOR EDGE ORANGE FOR IMPORTS TO IMPORTER SELECTION
                edge_color = "#ff7f0e"
            else:
                edge_color = "grey"
            lon0, lat0 = node_pos[src]
            lon1, lat1 = node_pos[dst]
            weight = self.graph[src][dst].get("Weight", 1)
            width = max(1, weight * 0.01)  # scaling

            edge_trace = go.Scattergeo(
                lon=[lon0, lon1],
                lat=[lat0, lat1],
                mode="lines",
                line=dict(width=width, color=edge_color),
                opacity=0.75,
                showlegend=False,
                hoverinfo="none",
            )
            edge_traces.append(edge_trace)

        # Build node trace
        node_lons = [node_pos[node][0] for node in self.graph.nodes()]
        node_lats = [node_pos[node][1] for node in self.graph.nodes()]
        node_trace = go.Scattergeo(
            lon=node_lons,
            lat=node_lats,
            mode="markers",
            marker=dict(size=node_sizes, color=node_colors, opacity=0.75),
            line=dict(color='rgb(0,0,0)', width=0),
            text=node_names,
            hoverinfo="text",
            showlegend=False,
        )

        # Visualization
        self.map = go.Figure(edge_traces + [node_trace])
        self.map.update_layout(
            geo_scope="world",  # focuses on the whole world
            geo=dict(showland=True, landcolor="#a7c8a9", showcoastlines=False),
            plot_bgcolor="white",
        )

        return self.map
