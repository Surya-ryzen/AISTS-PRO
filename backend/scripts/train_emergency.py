"""Train an experimental emergency detector from a reviewed source-separated YOLO dataset."""
import argparse

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--data',required=True)
    parser.add_argument('--model',default='yolov8s.pt')
    parser.add_argument('--epochs',type=int,default=30)
    parser.add_argument('--name',default='emergency_experiment')
    args=parser.parse_args()
    import torch
    from ultralytics import YOLO
    torch.set_num_threads(4)
    YOLO(args.model).train(data=args.data,epochs=args.epochs,imgsz=320,batch=4,device='cpu',workers=0,
        freeze=10,project='runs/emergency',name=args.name,plots=False,patience=30,seed=42,
        deterministic=True,amp=False,cache=False)

if __name__=='__main__':main()
