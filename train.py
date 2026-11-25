from ultralytics import YOLO

#코랩사용


model = YOLO('yolo11m.pt')  # COCO 사전학습 가중치
results = model.train(
    data=DATA_YAML,
    epochs=200,
    imgsz=960,
    batch=8,
    device=0,
    workers=4,
    patience=40,
    optimizer='AdamW',
    lr0=0.001,
    cos_lr=True,
    close_mosaic=15,
    amp=True,
    project='/content/Poker_Training',
    name='combined_yolo11m',
    seed=42,
    deterministic=True,
    plots=True,
    save=True
)