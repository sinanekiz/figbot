"""Local offline behavior-cloning baseline. No serial, camera, upload or rollout."""
import argparse
import json
from pathlib import Path
import numpy as np
import torch
from torch import nn


class VisualJointPolicy(nn.Module):
    def __init__(self):
        super().__init__()
        self.vision = nn.Sequential(nn.Conv2d(3, 8, 5, 2, 2), nn.ReLU(),
            nn.Conv2d(8, 16, 3, 2, 1), nn.ReLU(), nn.Conv2d(16, 16, 3, 2, 1),
            nn.ReLU(), nn.AdaptiveAvgPool2d((6, 8)), nn.Flatten())
        self.head = nn.Sequential(nn.Linear(16*6*8+18, 128), nn.ReLU(), nn.Linear(128, 18))

    def forward(self, image, history):
        return self.head(torch.cat([self.vision(image), history.flatten(1)/4096.], 1)).reshape(-1, 3, 6)


def fit(images, history, delta, indices, epochs, seed):
    torch.manual_seed(seed)
    model = VisualJointPolicy()
    optimizer = torch.optim.AdamW(model.parameters(), lr=.001, weight_decay=.0001)
    generator = torch.Generator().manual_seed(seed)
    for epoch in range(epochs):
        order = indices[torch.randperm(len(indices), generator=generator)]
        for batch in order.split(64):
            prediction = model(images[batch], history[batch])
            loss = nn.functional.smooth_l1_loss(prediction, delta[batch]/128.)
            optimizer.zero_grad(); loss.backward(); optimizer.step()
        if epoch % 10 == 0 or epoch == epochs-1:
            print(json.dumps(dict(epoch=epoch+1,loss=float(loss.detach()))),flush=True)
    return model.eval()


def metrics(model, images, history, target, current, indices):
    with torch.no_grad():
        pred = torch.cat([model(images[b], history[b])*128.+current[b,None,:]
                          for b in indices.split(64)])
    truth = target[indices]
    errors = abs(pred-truth)
    baseline = abs(current[indices,None,:]-truth)
    return dict(mae_counts=float(errors.mean()),per_joint_mae_counts=errors.mean((0,1)).tolist(),
        max_error_counts=float(errors.max()),hold_position_baseline_mae_counts=float(baseline.mean()),
        better_than_hold_baseline=bool(errors.mean() < baseline.mean())), pred


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--dataset',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--epochs',type=int,default=60)
    args=parser.parse_args()
    if args.epochs < 1:parser.error('Positive epochs required')
    args.output.mkdir(parents=True,exist_ok=False)
    torch.set_num_threads(2)
    torch.use_deterministic_algorithms(True)
    data=np.load(args.dataset,allow_pickle=False)
    images=torch.from_numpy(data['images'].transpose(0,3,1,2).copy()).float()/255.
    history=torch.from_numpy(data['history']);target=torch.from_numpy(data['target'])
    current=torch.from_numpy(data['current']);delta=target-current[:,None,:]
    groups=data['group'];train=torch.from_numpy(np.flatnonzero(groups!=3));test=torch.from_numpy(np.flatnonzero(groups==3))
    if len(test)<20 or len(train)<60:raise ValueError('Insufficient clean train/held-out samples')
    print(json.dumps(dict(stage='HELD_OUT_CYCLE',train=len(train),test=len(test))),flush=True)
    evaluation_model=fit(images,history,delta,train,args.epochs,42)
    evaluated,pred=metrics(evaluation_model,images,history,target,current,test)
    torch.save(evaluation_model.state_dict(),args.output/'evaluation_weights.pt')
    np.savez_compressed(args.output/'held_out_predictions.npz',prediction=pred.numpy(),
        target=target[test].numpy(),time=data['times'][test.numpy()])
    print(json.dumps(dict(stage='HELD_OUT_RESULT',**evaluated)),flush=True)
    print(json.dumps(dict(stage='ALL_REVIEWED_CYCLES')),flush=True)
    all_indices=torch.arange(len(images))
    final=fit(images,history,delta,all_indices,args.epochs,42)
    fitted,_=metrics(final,images,history,target,current,all_indices)
    torch.save(final.state_dict(),args.output/'policy_weights.pt')
    card=dict(model='VisualJointPolicy: small CNN plus measured joint history, three future targets',
        torch_version=torch.__version__,epochs=args.epochs,seed=42,training_samples=len(images),
        validation='Fourth pickup within the SAME recording held out; not independent scene validation',
        held_out_cycle=evaluated,full_data_fit=fitted,policy_trained=True,
        input='RGB 128x96 and three measured six-joint states spaced 100ms',
        output='Three corrected position deltas in units of 128 encoder counts at +0.2,+0.4,+0.6s',
        required_behavior='Open gripper before approach; keep constant approach opening; close only at grasp',
        limitation='Synthetic corrected targets and one continuous scene; no learned phase gate or verified geometry',
        autonomous_replay_allowed=False,physical_validation='UNVERIFIED',
        deployment_status='OFFLINE_EXPERIMENT_ONLY' if evaluated['better_than_hold_baseline'] else 'REJECTED_HELD_OUT_CYCLE',
        route_candidates_are_separate_from_neural_policy=True,dataset=str(args.dataset.resolve()))
    (args.output/'model_card.json').write_text(json.dumps(card,indent=2))
    print(json.dumps(card),flush=True)


if __name__=='__main__':main()
