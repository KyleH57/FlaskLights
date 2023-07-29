import numpy as np
import matplotlib.pyplot as plt
from sklearn.preprocessing import StandardScaler
from minisom import MiniSom


def run_som(X_list, song_name, segments, debug=False):
    # Convert the list to a numpy array
    X = np.array(X_list)

    # Standardize the data to have zero mean and unit variance
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    # Set the dimensions of the SOM
    map_width = 20
    map_height = 20
    input_len = X_scaled.shape[1]

    # Initialize the SOM
    som = MiniSom(map_width, map_height, input_len, sigma=1.0, learning_rate=0.5)

    # Train the SOM
    som.pca_weights_init(X_scaled) # Neural network go brr
    som.train_random(X_scaled, 1000)  # number of training iterations

    # Assign each sound vector to a cluster
    cluster_labels = np.zeros(X.shape[0], dtype=int)
    for i, x in enumerate(X_scaled):
        cluster_labels[i] = som.winner(x)[0]


    # Count the number of vectors in each cluster
    unique_labels, counts = np.unique(cluster_labels, return_counts=True)
    label_counts = dict(zip(unique_labels, counts))

    # Print the top n largest clusters with at least m vectors
    n = 5  # number of largest clusters to print
    m = 10  # minimum number of vectors per cluster
    sorted_counts = sorted(label_counts.items(), key=lambda x: x[1], reverse=True)
    top_n_clusters = [x[0] for x in sorted_counts[:n]]
    for cluster_label in top_n_clusters:
        if label_counts[cluster_label] >= m:
            cluster_coords = som.winner(som._weights[cluster_label])

            if debug:
                print("Cluster", cluster_label, "has", label_counts[cluster_label], "vectors")

                print("Cluster", cluster_label, "centroid coordinates:", cluster_coords)

    # Generate a list that corresponds to the top n clusters
    cluster_list = [-1] * len(segments)
    for i, segment in enumerate(segments):
        if cluster_labels[i] in top_n_clusters and label_counts[cluster_labels[i]] >= m:
            cluster_list[i] = cluster_labels[i]

    # Print the X,Y coordinates that each vector gets mapped to
    SOM_stuff_idk = []
    for i, x in enumerate(X_scaled):
        winner_coords = som.winner(x)
        # print("Vector", i, "is mapped to", winner_coords)
        SOM_stuff_idk.append(winner_coords)



    # Plot the SOM
    plt.figure(figsize=(map_width, map_height))
    plt.pcolor(som.distance_map().T, cmap='bone_r')
    plt.colorbar()

    # Plot the cluster centroids
    for cluster_label in top_n_clusters:
        if label_counts[cluster_label] >= m:
            cluster_coords = som.winner(som._weights[cluster_label])
            plt.plot(cluster_coords[1] + 0.5, cluster_coords[0] + 0.5, marker='o', markersize=15, color='red')

    if debug:
        # Save the plot to a file
        plt.savefig('SOM_images/som_plot_' + str(song_name) + '.png')

        # print the length of the segments array
        print("segments length: " + str(len(segments)))

        # print the length of the cluster list
        print("cluster list length: " + str(len(cluster_list)))

        # print("cluster_labels")
        # print(cluster_labels)

        # Print the number of clusters
        num_clusters = len(np.unique(cluster_labels))


    return SOM_stuff_idk
