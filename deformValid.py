import os
import torch
from pytorch3d.io import load_obj, save_obj
from pytorch3d.structures import Meshes
from pytorch3d.utils import ico_sphere
from pytorch3d.ops import sample_points_from_meshes
from torch.utils.tensorboard import SummaryWriter
import argparse
import numpy as np
from tqdm import tqdm
from mpl_toolkits.mplot3d import Axes3D
import matplotlib.pyplot as plt
import matplotlib as mpl
from nvp_cadex import NVP_v2_5_frame
from torch.utils.data import Dataset
from pytorch3d.loss import (
    chamfer_distance, 
    mesh_edge_loss, 
    mesh_laplacian_smoothing, 
    mesh_normal_consistency,
)
import trimesh
from dataset_meshes import Dataset_mesh, Dataset_mesh_objects, collate_fn
from torch.utils.data import DataLoader
import random
from foldingNet_model import AutoEncoder
import torch.nn.init as init
from modelAya import Autoencoder
import open3d as o3d
import torch.optim as optim
from torch.optim.lr_scheduler import CosineAnnealingLR


#deformed_model = './nvp_2018_1024dim_ycb_cosinusAneal_50/'
config='6'

B = 4
#path_autoencoder='/home/elham/Desktop/point-cloud-autoencoder/auto2018_1024dim_3000points_NoAug_1seq_5ycb/models/check_min.pt'

#path_autoencoder='/home/elham/Desktop/FoldingNet/first_50_each/logs/model_epoch_9000.pth'

#print('after')
#print('path:' ,path)

#print('here')
parser = argparse.ArgumentParser(description="Just an example", formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-l", "--load", action="store_true", help="checksum blocksize")
parser.add_argument('--k', "--k", type=int, default=1024)
parser.add_argument('--encoder_type', type=str, default='folding')

args = vars(parser.parse_args())

#loss_mean:  tensor(0.0010, device='cuda:0')
if(config == "0"):
    deformed_model = '/home/elham/Desktop/tutorials/fitMesh/cadex_nvp_pointnetEncoder2018paper_3000points_256Dim_noAug_minEncoder_ycb_5_1seq/'
    path_autoencoder='/home/elham/Desktop/point-cloud-autoencoder/auto2018_256dim_3000points_NoAug_1seq_5ycb/models/check_min.pt'
    trg_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/val/'
    src_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/in'
    args["k"]=256
    coeff = 2
#loss_mean:  tensor(0.0010, device='cuda:0')
elif(config == "1"):
    deformed_model = '/home/elham/Desktop/FoldingNet/nvp_2018_1024dim_ycb_cosinusAneal_50/'
    path_autoencoder='/home/elham/Desktop/point-cloud-autoencoder/auto2018_1024dim_3000points_NoAug_1seq_5ycb/models/check_min.pt'
    trg_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/val/'
    src_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/in'
    args["k"]=1024
    coeff = 8
#loss_mean:  tensor(0.0014, device='cuda:0')
elif(config == "2"):
    deformed_model = '/home/elham/Desktop/FoldingNet/nvp_folding_256dim_ycb_cosinusAneal_50/'
    path_autoencoder='/home/elham/Desktop/FoldingNet/first_50_each_folding_3000_256dim/logs/model_lowest_cd_loss.pth'
    trg_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/val/'
    src_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/in'
    args["k"]=256
    coeff = 2
#loss_mean:  tensor(0.0015, device='cuda:0')
elif(config == "3"):
    deformed_model = '/home/elham/Desktop/FoldingNet/nvp_folding_1024dim_ycb_cosinusAneal_50/'
    path_autoencoder='/home/elham/Desktop/FoldingNet/first_50_each_folding_3000_1024dim/logs/model_lowest_cd_loss.pth'
    trg_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/val/'
    src_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/in'
    args["k"]=1024
    coeff = 8
#loss_mean:  tensor(0.0014, device='cuda:0')
elif(config == "4"):
    deformed_model = '/home/elham/Desktop/FoldingNet/nvp_folding_1024dim_ycb_cosinusAneal_50End2End/'
    trg_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/val/'
    src_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/in'
    #path_autoencoder='/home/elham/Desktop/FoldingNet/first_50_each_folding_3000_1024dim/logs/model_lowest_cd_loss.pth'
    args["k"]=1024
    coeff = 8
#loss_mean:  tensor(0.0010, device='cuda:0')
elif(config == "5"):
    deformed_model = '/home/elham/Desktop/FoldingNet/nvp_2018_1024dim_ycb_cosinusAneal_50End/'
    trg_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/val/'
    src_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/in'
    #path_autoencoder='/home/elham/Desktop/point-cloud-autoencoder/auto2018_1024dim_3000points_NoAug_1seq_5ycb/models/check_min.pt'
    args["k"]=1024
    coeff = 8
#loss_mean:  tensor(0.0002, device='cuda:0')
elif(config == "6"):
    deformed_model = '/home/elham/Desktop/FoldingNet/nvp_2018_1024dim_ycb_1seq_sc_cosinusAneal_50_End2End/'
    trg_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/val_sc/'
    src_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_5_one_seq/in'
    #path_autoencoder='/home/elham/Desktop/FoldingNet/first_50_each_folding_3000_1024dim/logs/model_lowest_cd_loss.pth'
    args["k"]=1024
    coeff = 8
#loss_mean:  tensor(0.0005, device='cuda:0')
elif(config == "7"):
    deformed_model = '/home/elham/Desktop/FoldingNet/nvp_2018_1024dim_ycb_1000seq_sc_cosinusAneal_20_End2End/'
    trg_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_1_thousand_seq/val/'
    src_root='/home/elham/Desktop/makeDataset/warping/warping_shapes_generation/build_path/ycb_mult_1_thousand_seq/in'
    #path_autoencoder='/home/elham/Desktop/point-cloud-autoencoder/auto2018_1024dim_3000points_NoAug_1seq_5ycb/models/check_min.pt'
    args["k"]=1024
    coeff = 8
path_load_check_decoder = deformed_model+'check/'+ 'check_min'+'.pt'
os.makedirs(deformed_model+ 'check', exist_ok=True)
os.makedirs(deformed_model + 'meshes_valid', exist_ok=True)
os.makedirs(deformed_model + 'meshes_trg_val', exist_ok=True)
os.makedirs(deformed_model + 'meshes_compare_deform_decode', exist_ok=True)


device='cuda:0'
valid_dataset = Dataset_mesh_objects(trg_root=trg_root, src_root=src_root)
valid_dataloader = DataLoader(valid_dataset, batch_size=B, shuffle=False, collate_fn=collate_fn)

if(config == "0" or config == "1" or config == "5" or config == "6" or config == "7"):
    args['encoder_type'] = "2018"
else:
    args['encoder_type'] = "folding"
print('args: ', args['load'])

print('k: ', args['k'])
print('encoder: ', args['encoder_type'])
# Set the device
if torch.cuda.is_available():
    device = torch.device("cuda:0")
else:
    device = torch.device("cpu")
    print("WARNING: CPU only, this will be slow!")

print('device: ', device)

writer = SummaryWriter(log_dir=deformed_model+'events/')
###########################################################################

#homeomorphism_decoder:
n_layers = 6
#dimension of the code
feature_dims = 128 #2^7 * 2^3
hidden_size = [128, 64, 32, 32, 32]
#the dimension of the coordinates to be projected onto
proj_dims = 128
code_proj_hidden_size = [128, 128, 128]
proj_type = 'simple'
block_normalize = True
normalization = False

#print('here1')
c_dim = 128
hidden_dim = 128

homeomorphism_decoder = NVP_v2_5_frame(n_layers=n_layers, feature_dims=feature_dims*coeff, hidden_size=hidden_size, proj_dims=proj_dims,\
code_proj_hidden_size=code_proj_hidden_size, proj_type=proj_type, block_normalize=block_normalize, normalization=normalization).to('cuda')



numOfPoints=3000
if(args['encoder_type'] == '2018'):
    network = Autoencoder(k=args['k'], num_points=numOfPoints).to(device)
elif(args['encoder_type'] == 'folding'):
    network = AutoEncoder(k=args['k'])
device = torch.device('cuda')
network.to(device)


#check_auto = torch.load(path_autoencoder)
#network.load_state_dict(check_auto["model_state_dict"])
if(not 'End' in deformed_model):
    check_auto = torch.load(path_autoencoder, map_location='cuda:0')
    #print('check_auto: ', check_auto['model_state_dict'].keys())
    if(args['encoder_type'] == '2018'):
        network.load_state_dict(check_auto["model"])
    else:
        #print(check_auto["model_state_dict"])
        network.load_state_dict(check_auto["model_state_dict"])

#optimizer = optim.Adam(homeomorphism_decoder.parameters(), lr=5e-4, weight_decay=1e-5)
#scheduler = CosineAnnealingLR(optimizer, T_max=10000, eta_min=1e-7)
#optimizer = torch.optim.SGD([homeomorphism_decoder.parameters()], lr=lr, momentum=0.0)

if(args['load']):
    checkpoint = torch.load(path_load_check_decoder, map_location='cuda:0')
    #homeomorphism_encoder.load_state_dict(checkpoint['encoder'])
    homeomorphism_decoder.load_state_dict(checkpoint['decoder'])
    #optimizer.load_state_dict(checkpoint['optimizer'])
    if('End' in deformed_model):
        if(args['encoder_type'] == '2018'):
            network.load_state_dict(checkpoint['network'])
        else:
            #print(check_auto["model_state_dict"])
            network.load_state_dict(checkpoint["network"])


Nepochs = 500000

w_chamfer = 1.0
#print('here3')
w_edge = 0 #1.0

w_normal = 1.0 #0.01

w_laplacian = 0 #1.0 #0.1

plot_period = 250

chamfer_losses = []
laplacian_losses = []
edge_losses = []
normal_losses = []


iteration = 0


losses = []
lossIndividus = {}
keys = {'scissor', 'bleach', 'hammer', 'orange', 'brick', 'dice'}
for key in keys:
    lossIndividus[key]=[]
#print('epoch:', epoch)
homeomorphism_decoder.eval()
import time
for i, item in enumerate(valid_dataloader):
    begin= time.time()

    num_points = item['num_points']
    num_faces = item['num_faces']
    B,_,_ = item['vertices_src'].shape
    trg_mesh_verts_rightSize = [item['vertices_trg'][s][:num_points[s]]for s in range(B)]
    trg_mesh_faces_rightSize = [item['faces_trg'][s][:num_faces[s]]for s in range(B)]

    src_mesh_verts_rightSize = [item['vertices_src'][s][:num_points[s]]for s in range(B)]
    src_mesh_faces_rightSize = [item['faces_src'][s][:num_faces[s]]for s in range(B)]

    trg_mesh = Meshes(verts=trg_mesh_verts_rightSize, faces=trg_mesh_faces_rightSize)
    src_mesh = Meshes(verts=src_mesh_verts_rightSize, faces=src_mesh_faces_rightSize)
    
    seq_pc_trg = sample_points_from_meshes(trg_mesh, numOfPoints).to('cuda')
    seq_pc_src = sample_points_from_meshes(src_mesh, numOfPoints).to('cuda')

    begCode= time.time()
    with torch.no_grad():
        #print('seq_pc_trg shape: ', seq_pc_trg.shape)
        if(args['encoder_type'] == '2018'):
            code_trg , _ = network(seq_pc_trg.permute(0, 2, 1))
        else:
            code_trg = network.encoder(seq_pc_trg.permute(0, 2, 1))
        #code_trg = network.encoder(seq_pc_trg.permute(0, 2, 1))
    endCode= time.time()
    print('time coding: ', endCode-begCode)
    
    #print('code_trg.shape: ', code_trg.shape)
    b, k = code_trg.shape

    query = item['vertices_src'].to('cuda')

    #print('code trg shape: ', code_trg.shape)
    #print('query shape: ', query.shape)
    begDef= time.time()
    with torch.no_grad():
        coordinates = homeomorphism_decoder.forward(code_trg, query)
    endDef= time.time()

    #print('coordinates shape: ', coordinates.shape)
    coordinates = coordinates.reshape(B, 9000, 3)

    new_src_mesh_verts_rightSize = [coordinates[s][:num_points[s]]for s in range(B)]
    new_src_mesh_faces_rightSize = [item['faces_src'][s][:num_faces[s]].to('cuda') for s in range(B)]

    new_src_mesh = Meshes(verts=new_src_mesh_verts_rightSize, faces=new_src_mesh_faces_rightSize)
    end = time.time()

    print('time: ', end-begin)
    print('time def: ', endDef-begDef)

    numberOfSampledPoints=5000
    sample_trg = sample_points_from_meshes(trg_mesh, numberOfSampledPoints).to('cuda')
    new_sample_src = sample_points_from_meshes(new_src_mesh, numberOfSampledPoints).to('cuda')


    loss_chamfer, _ = chamfer_distance(sample_trg, new_sample_src)
    #loss_chamfer, _ = chamfer_distance(trg_mesh, new_src_mesh)
    loss = loss_chamfer * w_chamfer
    print('loss: ',loss)
    losses.append(loss)


    #loss.backward()

    #scheduler.step()


    #final_verts, final_faces = new_src_mesh.get_mesh_verts_faces(0)
    loss
    for i_item in range(B):
        name = item['name'][i_item]
        for key in keys:
            if(key in name):
                ls = chamfer_distance(sample_trg[i_item].unsqueeze(0), new_sample_src[i_item].unsqueeze(0))
                #print(key, ' ', lossIndividus)
                lossIndividus[key].append(ls[0].cpu())
        scale_trg = item['scale_obj'][i_item].to(device)
        center_trg = item['center_obj'][i_item].to(device)
        final_verts, final_faces = new_src_mesh.get_mesh_verts_faces(i_item)
        final_verts = final_verts * scale_trg + center_trg
        final_obj = os.path.join(deformed_model+'meshes_valid/', 'mesh_'+name.split('.')[0]+'_'+'.obj')
        save_obj(final_obj, final_verts, final_faces)

        final_verts_trg, final_faces_trg = trg_mesh.to(device).get_mesh_verts_faces(i_item)
        final_verts_trg = final_verts_trg * scale_trg + center_trg
        final_obj_trg = os.path.join(deformed_model+'meshes_trg_val/', 'trg_mesh_'+name.split('.')[0]+'_'+'.obj')
        save_obj(final_obj_trg, final_verts_trg, final_faces_trg)

for key in keys:
    if(len(lossIndividus[key])==0):
        print('does not exist')
    else:    
        print('loss for key: ', key, sum(lossIndividus[key])/len(lossIndividus[key]))

print('len: ', len(losses))
loss_mean = sum(losses) / len(losses)
print('loss_mean: ', loss_mean)
