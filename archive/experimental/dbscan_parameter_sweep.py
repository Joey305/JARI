




# import pandas as pd
# import numpy as np
# from sklearn.cluster import DBSCAN
# import matplotlib.pyplot as plt
# import networkx as nx
# import os
# import shutil
# import umap.umap_ as umap  # UMAP library
# from itertools import product

# # Load the average DockQ scores into a DataFrame
# csv_file_path = 'Averaged_DockQ_Scores.csv'  # Update this with the actual path to your CSV file
# average_dockq = pd.read_csv(csv_file_path)

# # Split the 'key' column into two new columns for model PDB identifiers
# average_dockq[['Model_PDB1', 'Model_PDB2']] = average_dockq['key'].str.split('-', expand=True)

# # Create a unique list of all models involved in comparisons
# unique_models = pd.unique(average_dockq[['Model_PDB1', 'Model_PDB2']].values.ravel('K'))

# # Create a mapping from model keys to indices
# model_to_index = {model: idx for idx, model in enumerate(unique_models)}
# index_to_model_PDB = {idx: model for model, idx in model_to_index.items()}  # Reverse mapping

# # Initialize a square distance matrix
# distance_matrix = np.ones((len(unique_models), len(unique_models)))  # Start with a matrix of ones

# # Populate the distance matrix with distances (1 - Average_DockQ)
# for _, row in average_dockq.iterrows():
#     idx1 = model_to_index[row['Model_PDB1']]
#     idx2 = model_to_index[row['Model_PDB2']]
#     distance = 1 - row['Average_DockQ']  # Calculate the distance
#     # Symmetrically assign the distance for both model pairs
#     distance_matrix[idx1, idx2] = distance
#     distance_matrix[idx2, idx1] = distance

# # # Lists of parameters
# eps_values = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.09, 0.10, 0.11, 0.12, 0.13, 0.14, 0.15, 0.16, 0.17, 0.18, 0.19, 0.20],# 0.21, 0.22, 0.23, 0.24, 0.25, 0.26, 0.27, 0.28, 0.29, 0.30, 0.31, 0.32, 0.33, 0.34, 0.35, 0.36, 0.37, 0.38, 0.39, 0.40, 0.41, 0.42, 0.43, 0.44, 0.45, 0.46, 0.47, 0.48, 0.49, 0.50, 0.51, 0.52, 0.53, 0.54, 0.55, 0.56, 0.57, 0.58, 0.59, 0.60, 0.61, 0.62, 0.63, 0.64, 0.65, 0.66, 0.67, 0.68, 0.69, 0.70, 0.71, 0.72, 0.73, 0.74, 0.75, 0.9, 0.99]  # Epsilon values for DBSCAN
# min_samples_values = [2,3,4]  # Minimum number of samples for a cluster
# min_cluster_members_values = [2, 5, 10, 15]  # Minimum number of members in a cluster for UMAP visualization

# # DBSCAN clustering
# for eps_value, min_samples_value, min_cluster_members in product(eps_values, min_samples_values, min_cluster_members_values):
#     db = DBSCAN(eps=eps_value, min_samples=min_samples_value, metric="precomputed")
#     cluster_labels = db.fit_predict(distance_matrix)

#     # Create a DataFrame for the cluster assignments
#     cluster_assignments = pd.DataFrame({
#         'Model_PDB': [index_to_model_PDB[i] for i in range(len(cluster_labels))],
#         'Cluster': cluster_labels
#     })

#     # Extract model names from the 'Model_PDB' field
#     cluster_assignments['Model_Name'] = cluster_assignments['Model_PDB'].apply(lambda x: x.split('_combined')[0])

#     # Analyze cluster results
#     cluster_summary = cluster_assignments['Cluster'].value_counts().sort_index()
#     # Exclude the noise cluster and sort by the number of models in each cluster
#     cluster_summary_sorted = cluster_summary[cluster_summary.index != -1].sort_values(ascending=False)

#     number_of_clusters_generated = cluster_summary_sorted.count()
#     number_of_unclustered_models = cluster_summary[cluster_summary.index == -1].values[0] if -1 in cluster_summary else 0

#     # Print cluster summary in descending order
#     print(f"Total number of clusters generated: {number_of_clusters_generated}")
#     print("Number of models in each cluster (sorted in descending order):")
#     print(cluster_summary_sorted)
#     print(f"Number of unclustered models (noise): {number_of_unclustered_models}")

#     # Save the cluster assignments to a CSV file
#     output_csv_filename = f"NEW_Cluster_Assignments_eps{eps_value}_minsamp{min_samples_value}.csv"
#     cluster_assignments.to_csv(output_csv_filename, index=False)
#     print(f"Cluster assignments saved to {output_csv_filename}.")

#     # Directory to save the figures
#     figures_dir = "AbrilNEW_clustering_figures"
#     os.makedirs(figures_dir, exist_ok=True)

#     # Plot UMAP for clusters with a minimum number of members
#     valid_clusters = cluster_summary_sorted[cluster_summary_sorted >= min_cluster_members].index

#     # Filter out unclustered models
#     cluster_assignments_filtered = cluster_assignments[cluster_assignments['Cluster'].isin(valid_clusters)]

#     # Exclude the unclustered group
#     cluster_assignments_filtered = cluster_assignments_filtered[cluster_assignments_filtered['Cluster'] != -1]

#     # Extract embeddings using UMAP
#     reducer = umap.UMAP()
#     embeddings = reducer.fit_transform(distance_matrix)

#     # Plot UMAP
#     plt.figure(figsize=(10, 8))
#     for cluster_id in valid_clusters:
#         cluster_indices = cluster_assignments_filtered[cluster_assignments_filtered['Cluster'] == cluster_id].index
#         plt.scatter(embeddings[cluster_indices, 0], embeddings[cluster_indices, 1], label=f'Cluster {cluster_id}', alpha=0.5)

#     plt.title(f'UMAP Visualization (eps={eps_value}, min_samples={min_samples_value}, min_cluster_members={min_cluster_members})')
#     plt.xlabel('UMAP Dimension 1')
#     plt.ylabel('UMAP Dimension 2')
#     plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')  # Position legend outside the plot area
#     umap_plot_filename = os.path.join(figures_dir, f'NEW_UMAP_eps{eps_value}_minsamp{min_samples_value}_minmembers{min_cluster_members}.png')
#     plt.savefig(umap_plot_filename, bbox_inches='tight')  # Ensure legend is not clipped
#     print(f"UMAP plot saved to {umap_plot_filename}.")

#     plt.show()









# import pandas as pd
# import numpy as np
# from sklearn.cluster import DBSCAN
# import matplotlib.pyplot as plt
# import networkx as nx
# import os
# import shutil
# import umap.umap_ as umap  # UMAP library


# # Load the average DockQ scores into a DataFrame
# csv_file_path = 'Averaged_DockQ_Scores.csv'  # Update this with the actual path to your CSV file
# average_dockq = pd.read_csv(csv_file_path)

# # Split the 'key' column into two new columns for model PDB identifiers
# average_dockq[['Model_PDB1', 'Model_PDB2']] = average_dockq['key'].str.split('-', expand=True)

# # Create a unique list of all models involved in comparisons
# unique_models = pd.unique(average_dockq[['Model_PDB1', 'Model_PDB2']].values.ravel('K'))

# # Create a mapping from model keys to indices
# model_to_index = {model: idx for idx, model in enumerate(unique_models)}
# index_to_model_PDB = {idx: model for model, idx in model_to_index.items()}  # Reverse mapping

# # Initialize a square distance matrix
# distance_matrix = np.ones((len(unique_models), len(unique_models)))  # Start with a matrix of ones

# # Populate the distance matrix with distances (1 - Average_DockQ)
# for _, row in average_dockq.iterrows():
#     idx1 = model_to_index[row['Model_PDB1']]
#     idx2 = model_to_index[row['Model_PDB2']]
#     distance = 1 - row['Average_DockQ']  # Calculate the distance
#     # Symmetrically assign the distance for both model pairs
#     distance_matrix[idx1, idx2] = distance
#     distance_matrix[idx2, idx1] = distance

# # DBSCAN clustering parameters
# eps_value = 0.2  # Epsilon value for DBSCAN
# min_samples_value = 1  # Minimum number of samples for a cluster

# db = DBSCAN(eps=eps_value, min_samples=min_samples_value, metric="precomputed")
# cluster_labels = db.fit_predict(distance_matrix)

# # Create a DataFrame for the cluster assignments
# cluster_assignments = pd.DataFrame({
#     'Model_PDB': [index_to_model_PDB[i] for i in range(len(cluster_labels))],
#     'Cluster': cluster_labels
# })

# # Extract model names from the 'Model_PDB' field
# cluster_assignments['Model_Name'] = cluster_assignments['Model_PDB'].apply(lambda x: x.split('_combined')[0])

# # Analyze cluster results
# cluster_summary = cluster_assignments['Cluster'].value_counts().sort_index()
# # Exclude the noise cluster and sort by the number of models in each cluster
# cluster_summary_sorted = cluster_summary[cluster_summary.index != -1].sort_values(ascending=False)

# number_of_clusters_generated = cluster_summary_sorted.count()
# number_of_unclustered_models = cluster_summary[cluster_summary.index == -1].values[0] if -1 in cluster_summary else 0

# # Print cluster summary in descending order
# print(f"Total number of clusters generated: {number_of_clusters_generated}")
# print("Number of models in each cluster (sorted in descending order):")
# print(cluster_summary_sorted)
# print(f"Number of unclustered models (noise): {number_of_unclustered_models}")

# # Save the cluster assignments to a CSV file
# output_csv_filename = f"Cluster_Assignments_eps{eps_value}_minsamp{min_samples_value}.csv"
# cluster_assignments.to_csv(output_csv_filename, index=False)
# print(f"Cluster assignments saved to {output_csv_filename}.")

# # Find the top cluster (with the most models)
# top_cluster = cluster_assignments['Cluster'].value_counts().idxmax()

# # Filter models that belong to the top cluster
# top_cluster_models = cluster_assignments[cluster_assignments['Cluster'] == top_cluster]

# # Count the occurrence of each model in the top cluster
# model_counts = top_cluster_models['Model_Name'].value_counts()

# # Read the Excel sheet for legend
# legend_path = 'Model_PDB_Legend_Mapping.xlsx'
# legend_df = pd.read_excel(legend_path, sheet_name='Legend')

# # Create a mapping dictionary from the legend
# code_model_mapping = pd.Series(legend_df.Code.values, index=legend_df.Model).to_dict()

# # Update the 'Model_Name' field with codes from the legend
# cluster_assignments['Model_Code'] = cluster_assignments['Model_Name'].map(code_model_mapping)

# # Filter models that belong to the top cluster
# top_cluster_models = cluster_assignments[cluster_assignments['Cluster'] == top_cluster]

# # Count the occurrence of each model in the top cluster, using the coded names
# model_counts = top_cluster_models['Model_Code'].value_counts()

# # Create a network graph for the models in the top cluster using the coded names
# G = nx.Graph()
# for model_code, count in model_counts.items():
#     G.add_node(model_code, size=count)

# # Add edges between the models if they are in the same cluster, using the coded names
# for _, row in average_dockq.iterrows():
#     model_code1 = code_model_mapping.get(row['Model_PDB1'].split('_combined')[0])
#     model_code2 = code_model_mapping.get(row['Model_PDB2'].split('_combined')[0])
#     if model_code1 and model_code2 and model_code1 in model_counts and model_code2 in model_counts:
#         G.add_edge(model_code1, model_code2)

# # Directory to save the figures
# figures_dir = "clustering_figures"
# os.makedirs(figures_dir, exist_ok=True)

# # Plot UMAP for clusters with a minimum number of members
# min_cluster_members = 10  # Minimum number of members in a cluster for visualization
# valid_clusters = cluster_summary_sorted[cluster_summary_sorted >= min_cluster_members].index

# # Filter out unclustered models
# cluster_assignments_filtered = cluster_assignments[cluster_assignments['Cluster'].isin(valid_clusters)]

# # Exclude the unclustered group
# cluster_assignments_filtered = cluster_assignments_filtered[cluster_assignments_filtered['Cluster'] != -1]

# # Extract embeddings using UMAP
# reducer = umap.UMAP()
# embeddings = reducer.fit_transform(distance_matrix)

# # Plot UMAP for clusters with a minimum number of members and excluding cluster 0
# min_cluster_members = 5  # Minimum number of members in a cluster for visualization
# valid_clusters = cluster_summary_sorted[(cluster_summary_sorted >= min_cluster_members) & (cluster_summary_sorted.index != 0)].index

# # Filter out unclustered models and cluster 0
# cluster_assignments_filtered = cluster_assignments[cluster_assignments['Cluster'].isin(valid_clusters)]

# # Extract embeddings using UMAP
# reducer = umap.UMAP()
# embeddings = reducer.fit_transform(distance_matrix)

# # Plot UMAP for clusters with a minimum number of members and excluding cluster 0
# min_cluster_members = 10  # Minimum number of members in a cluster for visualization
# valid_clusters = cluster_summary_sorted[(cluster_summary_sorted >= min_cluster_members) & (cluster_summary_sorted.index != 0)].index

# # Filter out unclustered models and cluster 0
# cluster_assignments_filtered = cluster_assignments[cluster_assignments['Cluster'].isin(valid_clusters)]

# # Extract embeddings using UMAP
# reducer = umap.UMAP()
# embeddings = reducer.fit_transform(distance_matrix)

# # Plot UMAP
# plt.figure(figsize=(10, 8))
# for cluster_id in valid_clusters:
#     cluster_indices = cluster_assignments_filtered[cluster_assignments_filtered['Cluster'] == cluster_id].index
#     plt.scatter(embeddings[cluster_indices, 0], embeddings[cluster_indices, 1], label=f'Cluster {cluster_id}', alpha=0.5)

# plt.title(f'UMAP Visualization (eps={eps_value}, min_samples={min_samples_value}, min_cluster_members={min_cluster_members})')
# plt.xlabel('UMAP Dimension 1')
# plt.ylabel('UMAP Dimension 2')
# plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')  # Position legend outside the plot area
# umap_plot_filename = os.path.join(figures_dir, f'UMAP_eps{eps_value}_minsamp{min_samples_value}_minmembers{min_cluster_members}.png')
# plt.savefig(umap_plot_filename, bbox_inches='tight')  # Ensure legend is not clipped
# print(f"UMAP plot saved to {umap_plot_filename}.")

# plt.show()






import pandas as pd
import numpy as np
from sklearn.cluster import DBSCAN
import matplotlib.pyplot as plt
import networkx as nx
import os
import shutil



# Load the average DockQ scores into a DataFrame
csv_file_path = 'Averaged_DockQ_Scores.csv'  # Update this with the actual path to your CSV file
average_dockq = pd.read_csv(csv_file_path)

# Split the 'key' column into two new columns for model PDB identifiers
average_dockq[['Model_PDB1', 'Model_PDB2']] = average_dockq['key'].str.split('-', expand=True)

# Create a unique list of all models involved in comparisons
unique_models = pd.unique(average_dockq[['Model_PDB1', 'Model_PDB2']].values.ravel('K'))

# Create a mapping from model keys to indices
model_to_index = {model: idx for idx, model in enumerate(unique_models)}
index_to_model_PDB = {idx: model for model, idx in model_to_index.items()}  # Reverse mapping

# Initialize a square distance matrix
distance_matrix = np.ones((len(unique_models), len(unique_models)))  # Start with a matrix of ones

# Populate the distance matrix with distances (1 - Average_DockQ)
for _, row in average_dockq.iterrows():
    idx1 = model_to_index[row['Model_PDB1']]
    idx2 = model_to_index[row['Model_PDB2']]
    distance = 1 - row['Average_DockQ']  # Calculate the distance
    # Symmetrically assign the distance for both model pairs
    distance_matrix[idx1, idx2] = distance
    distance_matrix[idx2, idx1] = distance

# DBSCAN clustering parameters
eps_value = 0.05  # Epsilon value for DBSCAN
min_samples_value = 1  # Minimum number of samples for a cluster

db = DBSCAN(eps=eps_value, min_samples=min_samples_value, metric="precomputed")
cluster_labels = db.fit_predict(distance_matrix)

# Create a DataFrame for the cluster assignments
cluster_assignments = pd.DataFrame({
    'Model_PDB': [index_to_model_PDB[i] for i in range(len(cluster_labels))],
    'Cluster': cluster_labels
})

# Extract model names from the 'Model_PDB' field
cluster_assignments['Model_Name'] = cluster_assignments['Model_PDB'].apply(lambda x: x.split('_combined')[0])

# Analyze cluster results
cluster_summary = cluster_assignments['Cluster'].value_counts().sort_index()
# Exclude the noise cluster and sort by the number of models in each cluster
cluster_summary_sorted = cluster_summary[cluster_summary.index != -1].sort_values(ascending=False)

number_of_clusters_generated = cluster_summary_sorted.count()
number_of_unclustered_models = cluster_summary[cluster_summary.index == -1].values[0] if -1 in cluster_summary else 0

# Print cluster summary in descending order
print(f"Total number of clusters generated: {number_of_clusters_generated}")
print("Number of models in each cluster (sorted in descending order):")
print(cluster_summary_sorted)
print(f"Number of unclustered models (noise): {number_of_unclustered_models}")

# Save the cluster assignments to a CSV file
output_csv_filename = f"Cluster_Assignments_eps{eps_value}_minsamp{min_samples_value}.csv"
cluster_assignments.to_csv(output_csv_filename, index=False)
print(f"Cluster assignments saved to {output_csv_filename}.")

# Find the top cluster (with the most models)
top_cluster = cluster_assignments['Cluster'].value_counts().idxmax()

# Filter models that belong to the top cluster
top_cluster_models = cluster_assignments[cluster_assignments['Cluster'] == top_cluster]

# Count the occurrence of each model in the top cluster
model_counts = top_cluster_models['Model_Name'].value_counts()

# Read the Excel sheet for legend
legend_path = 'Model_PDB_Legend_Mapping.xlsx'
legend_df = pd.read_excel(legend_path, sheet_name='Legend')

# Create a mapping dictionary from the legend
code_model_mapping = pd.Series(legend_df.Code.values, index=legend_df.Model).to_dict()

# Update the 'Model_Name' field with codes from the legend
cluster_assignments['Model_Code'] = cluster_assignments['Model_Name'].map(code_model_mapping)

# Filter models that belong to the top cluster
top_cluster_models = cluster_assignments[cluster_assignments['Cluster'] == top_cluster]

# Count the occurrence of each model in the top cluster, using the coded names
model_counts = top_cluster_models['Model_Code'].value_counts()

# Create a network graph for the models in the top cluster using the coded names
G = nx.Graph()
for model_code, count in model_counts.items():
    G.add_node(model_code, size=count)

# Add edges between the models if they are in the same cluster, using the coded names
for _, row in average_dockq.iterrows():
    model_code1 = code_model_mapping.get(row['Model_PDB1'].split('_combined')[0])
    model_code2 = code_model_mapping.get(row['Model_PDB2'].split('_combined')[0])
    if model_code1 and model_code2 and model_code1 in model_counts and model_code2 in model_counts:
        G.add_edge(model_code1, model_code2)

# Directory to save the figures
figures_dir = "clustering_figures"
os.makedirs(figures_dir, exist_ok=True)

plt.figure(figsize=(12, 12))
pos = nx.spring_layout(G)  # positions for all nodes
node_sizes = [G.nodes[node]['size'] * 100 for node in G]  # Node size based on count
node_colors = ['gold' if node in model_counts.head(5) else 'lightblue' for node in G]  # Color top 5 differently
nx.draw_networkx_nodes(G, pos, node_size=node_sizes, node_color=node_colors)
nx.draw_networkx_edges(G, pos)

# Draw the labels with the node codes and sizes (count 'N')
node_labels = {node: f"{node}\n({G.nodes[node]['size']})" for node in G}
nx.draw_networkx_labels(G, pos, labels=node_labels, font_size=8, font_color='black', font_weight='bold', horizontalalignment='center', verticalalignment='center')

plt.title("Network Graph of Models in the Top Cluster (Coded)")
plt.axis('off')
network_graph_coded_filename =os.path.join(figures_dir,f"Network_Graph_Coded_eps{eps_value}_minsamp{min_samples_value}.png")
plt.savefig(network_graph_coded_filename)
print(f"Coded network graph with node letters and counts saved to {network_graph_coded_filename}.")


# Create the bar chart for the model counts
plt.figure(figsize=(12, 8))
model_counts.plot(kind='bar')
plt.title('Model Counts in the Top Cluster')
plt.xlabel('Model')
plt.ylabel('Count')

# Save the bar chart to a file
bar_chart_filename = os.path.join(figures_dir, f"Model_Counts_Bar_Chart_eps{eps_value}_minsamp{min_samples_value}.png")
plt.savefig(bar_chart_filename)
print(f"Bar chart saved to {bar_chart_filename}.")

# # Directory paths
# pdb_files_dir = "PDB_FILESNAMED"
# clustered_pdb_dir = f"CLUSTERED_PDB_FILES_eps{eps_value}_minsamp{min_samples_value}"

# # Create a directory for clustered pdb files
# os.makedirs(clustered_pdb_dir, exist_ok=True)

# # Iterate through each cluster
# for cluster_id in cluster_summary_sorted.index:
#     # Create a directory for the cluster
#     cluster_dir = os.path.join(clustered_pdb_dir, f"Cluster_{cluster_id}")
#     os.makedirs(cluster_dir, exist_ok=True)
    
#     # Filter models in the current cluster
#     cluster_models = cluster_assignments[cluster_assignments['Cluster'] == cluster_id]['Model_PDB']
    
#     # Move corresponding pdb files to the cluster directory
#     for model_pdb in cluster_models:
#         pdb_filename = os.path.join(pdb_files_dir, model_pdb)
#         if os.path.exists(pdb_filename):
#             shutil.move(pdb_filename, cluster_dir)

# # Move unclustered models to a directory named "Unclustered"
# unclustered_dir = os.path.join(clustered_pdb_dir, "Unclustered")
# os.makedirs(unclustered_dir, exist_ok=True)

# # Filter unclustered models
# unclustered_models = cluster_assignments[cluster_assignments['Cluster'] == -1]['Model_PDB']

# # Move unclustered pdb files to the "Unclustered" directory
# for model_pdb in unclustered_models:
#     pdb_filename = os.path.join(pdb_files_dir, model_pdb)
#     if os.path.exists(pdb_filename):
#         shutil.move(pdb_filename, unclustered_dir)

# print("PDB files clustered and moved.")
