import dgl
import torch as th
import os 
import numpy as np 

def load_reddit():
    from dgl.data import RedditDataset

    # load reddit data
    data = RedditDataset(self_loop=True)
    g = data[0]
    g.ndata['features'] = g.ndata['feat']
    g.ndata['labels'] = g.ndata['label']
    return g, data.num_classes

def load_ogb(name):
    from ogb.nodeproppred import DglNodePropPredDataset

    print('load', name)
    data = DglNodePropPredDataset(name=name)
    print('finish loading', name)
    splitted_idx = data.get_idx_split()
    graph, labels = data[0]
    labels = labels[:, 0]

    graph.ndata['features'] = graph.ndata['feat']
    graph.ndata['labels'] = labels
    in_feats = graph.ndata['features'].shape[1]
    num_labels = len(th.unique(labels[th.logical_not(th.isnan(labels))]))

    # Find the node IDs in the training, validation, and test set.
    train_nid, val_nid, test_nid = splitted_idx['train'], splitted_idx['valid'], splitted_idx['test']
    train_mask = th.zeros((graph.number_of_nodes(),), dtype=th.bool)
    train_mask[train_nid] = True
    val_mask = th.zeros((graph.number_of_nodes(),), dtype=th.bool)
    val_mask[val_nid] = True
    test_mask = th.zeros((graph.number_of_nodes(),), dtype=th.bool)
    test_mask[test_nid] = True
    graph.ndata['train_mask'] = train_mask
    graph.ndata['val_mask'] = val_mask
    graph.ndata['test_mask'] = test_mask
    print('finish constructing', name)
    return graph, num_labels

def load_custom(datadir):
    edgelist = np.load(os.path.join(datadir,'edgelist.npy')).astype(int)
    features = np.load(os.path.join(datadir,'features.npy'))
    features = th.tensor(features).float()
    labels = np.load(os.path.join(datadir,'labels.npy')).reshape((-1,))
    labels[labels==-1]=float('nan')
    labels = th.tensor(labels)
    splits = np.load(os.path.join(datadir,'splits.npy')).astype(int).reshape((-1,))

    n_nodes = labels.shape[0]
    graph = dgl.graph((edgelist[:,0], edgelist[:,1]), num_nodes=labels.shape[0])
    graph.ndata['features'] = features
    graph.ndata['labels'] = labels
    in_feats = graph.ndata['features'].shape[1]
    num_labels = len(th.unique(labels[th.logical_not(th.isnan(labels))]))

    train_mask = th.zeros(n_nodes, dtype=th.bool)
    val_mask = th.zeros(n_nodes, dtype=th.bool)
    test_mask = th.zeros(n_nodes, dtype=th.bool)
    train_mask[splits==1] = True
    val_mask[splits==2] = True
    test_mask[splits==3] = True
    graph.ndata['train_mask'] = train_mask
    graph.ndata['val_mask'] = val_mask
    graph.ndata['test_mask'] = test_mask
    print('finish constructing', datadir)

    return graph, num_labels

def inductive_split(g):
    """Split the graph into training graph, validation graph, and test graph by training
    and validation masks.  Suitable for inductive models."""
    train_g = g.subgraph(g.ndata['train_mask'])
    val_g = g.subgraph(g.ndata['train_mask'] | g.ndata['val_mask'])
    test_g = g
    return train_g, val_g, test_g
