import networkx as nx
import streamlit as st
import plotly.graph_objects as go
from pyvis.network import Network

class NetworkGraphBuilder:
    def __init__(self, data, countries, exporter_color='blue', importer_color='red', default_color='grey'):
        self.data = data  # DataFrame with columns for exporters, importers, quantity, countries
        self.countries = countries
        self.exporter_color = exporter_color
        self.importer_color = importer_color
        self.default_color = default_color
        self.graph = None
        self.map = None

    def build_graph(self, weighted=False):
        if weighted:
            self.graph = nx.from_pandas_edgelist(
                self.data,
                source='Exporter',
                target='Importer',
                edge_attr='Weight',
                create_using=nx.DiGraph()
            )
        else:
            self.graph = nx.from_pandas_edgelist(
                self.data,
                source='Exporter',
                target='Importer',
                create_using=nx.DiGraph()
            )
        return self.graph

    def scale_nodes(self, scale_method='degree'):
        if not self.graph:
            raise ValueError("Graph not built.")
        centrality_methods = {
            'degree': nx.degree_centrality,
            'indegree': nx.in_degree_centrality,
            'outdegree': nx.out_degree_centrality,
            'eigenvector': nx.eigenvector_centrality,
            'closeness': nx.closeness_centrality,
            'betweenness': nx.betweenness_centrality
        }
        if scale_method in centrality_methods:
            cent = centrality_methods[scale_method](self.graph)
            for node, value in cent.items():
                nx.set_node_attributes(self.graph, {node: value * 100}, 'size')
        return self.graph

    def color_nodes(self, exporters, importers):
        color_attr = {}
        for node in self.graph.nodes:
            if node in exporters:
                color_attr[node] = self.exporter_color
            elif node in importers:
                color_attr[node] = self.importer_color
            else:
                color_attr[node] = self.default_color
        nx.set_node_attributes(self.graph, color_attr, 'color')
        return self.graph

    def to_pyvis(self, height='900px', directed=True):
        net = Network(height=height, directed=directed)
        net.from_nx(self.graph)
        net.repulsion(node_distance=420, central_gravity=0.33, spring_length=110,
                      spring_strength=0.1, damping=0.95)
        return net

    def build_map(self, countries, exporter_sel, importer_sel):
        # Map country code to coordinates and names
        ex_code = exporter_sel
        im_code = importer_sel
        #node_pos = {row['country']: (row['longitude'], row['latitude']) for _, row in countries.iterrows()}
        node_pos = {}
        for node in self.graph.nodes():
            match = countries.loc[countries['country'] == node]
            if not match.empty:
                row = match.iloc[0]
                node_pos[node] = (row['longitude'], row['latitude'])
            else:
                node_pos[node] = (0, 0)
        print(node_pos)
        #node_names = [countries.loc[countries['country'] == node, 'name'].values[0] for node in self.graph.nodes()]
        node_names = []
        for node in self.graph.nodes():
            match = countries.loc[countries['country'] == node, 'name']
            node_names.append(match.values[0] if not match.empty else "XX")

        # Adjust node sizes 
        node_sizes = [self.graph.nodes[node].get('size', 8) for node in self.graph.nodes()]
        node_colors = [self.graph.nodes[node].get('color', 'grey') for node in self.graph.nodes()]

        #G = nx.spring_layout(species)  # substitute species with your graph variable
        #pos = nx.spring_layout(species)

        # Build edge traces for the network
        edge_traces = []
        for src, dst in self.graph.edges():
            if src == ex_code and dst == im_code:
                edge_color = 'blue'
            elif dst == im_code:
                edge_color = 'red'
            else:
                edge_color = 'grey'
            lon0, lat0 = node_pos[src]
            lon1, lat1 = node_pos[dst]
            weight = self.graph[src][dst].get('Weight', 1)
            width = max(1, weight * 0.01) # scaling

            edge_trace = go.Scattergeo(
                lon=[lon0, lon1],
                lat=[lat0, lat1],
                mode='lines',
                #line=dict(width=1, color='blue'),
                line=dict(width=width, color=edge_color),
                opacity=0.5,
                showlegend=False,
                hoverinfo='none'
            )
            edge_traces.append(edge_trace)

        # Build node trace
        node_lons = [node_pos[node][0] for node in self.graph.nodes()]
        node_lats = [node_pos[node][1] for node in self.graph.nodes()]
        node_trace = go.Scattergeo(
            lon=node_lons,
            lat=node_lats,
            mode='markers',
            #marker=dict(size=8, color='red'),
            marker=dict(size=node_sizes, color=node_colors),
            #text=[str(node) for node in species.nodes()],
            text=node_names,
            hoverinfo='text',
            showlegend=False,
        )

        # Visualization
        self.map = go.Figure(edge_traces + [node_trace])
        self.map.update_layout(
            geo_scope='world', # focuses on the whole world
            geo=dict(showland=True, landcolor='lightgray')
        )

        return self.map
