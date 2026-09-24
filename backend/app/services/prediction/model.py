"""Serializable ridge autoregression with chronological holdout and additive explanations."""
import numpy as np

METRICS = ('vehicle_count','average_speed','queue_length')
LAGS = 6


def fit(x,y):
    mean=x.mean(axis=0);scale=x.std(axis=0);scale[scale<1e-8]=1
    z=(x-mean)/scale
    design=np.column_stack([np.ones(len(z)),z])
    penalty=np.eye(design.shape[1]);penalty[0,0]=0
    weights=np.linalg.solve(design.T@design+penalty,design.T@y)
    return dict(mean=mean.tolist(),scale=scale.tolist(),weights=weights.tolist())


def predict(artifact,x):
    return np.maximum(0,np.column_stack([np.ones(len(x)),
        (x-np.array(artifact['mean']))/np.array(artifact['scale'])])@np.array(artifact['weights']))


def train(rows,horizon):
    if horizon not in (1,5,15):raise ValueError('Supported horizons are 1, 5 and 15 minutes.')
    if len(rows)<90+2*horizon:raise ValueError(f'Need at least {90+2*horizon} consecutive complete minute samples for training.')
    minutes=[r.minute for r in rows]
    if any(b-a!=1 for a,b in zip(minutes,minutes[1:])):raise ValueError('Training samples must be consecutive minutes from one source run.')
    data=np.array([[getattr(r,m) for m in METRICS] for r in rows],dtype=float)
    if not np.isfinite(data).all():raise ValueError('Measurements must be finite.')
    origins=np.arange(LAGS-1,len(rows)-horizon)
    x=np.array([data[i-LAGS+1:i+1].reshape(-1) for i in origins])
    y=data[origins+horizon]
    train_cut=int(len(rows)*.6);valid_cut=int(len(rows)*.8)
    a=origins+horizon<train_cut
    b=(origins>=train_cut)&(origins+horizon<valid_cut)
    c=origins>=valid_cut
    if min(a.sum(),b.sum(),c.sum())<5:raise ValueError('Insufficient chronological holdout samples for this horizon.')
    artifact=fit(x[a],y[a])
    validation=np.abs(predict(artifact,x[b])-y[b]).mean(axis=0)
    baseline_validation=np.abs(data[origins[b]]-y[b]).mean(axis=0)
    selected=['ridge' if validation[i]<baseline_validation[i] else 'last_value' for i in range(3)]
    test_ridge=predict(artifact,x[c]);test_naive=data[origins[c]]
    chosen=np.column_stack([test_ridge[:,i] if selected[i]=='ridge' else test_naive[:,i] for i in range(3)])
    # Refit deployable coefficients after model selection/evaluation; report held-out metrics separately.
    final=fit(x,y)
    final.update(schema_version=1,algorithm='ridge_autoregression',ridge_penalty=1.0,lags=LAGS,
        horizon=horizon,metrics=list(METRICS),selected=selected,
        evaluation=dict(split='chronological 60/20/20 with horizon gap',
          train_samples=int(a.sum()),validation_samples=int(b.sum()),test_samples=int(c.sum()),
          validation_mae=dict(zip(METRICS,validation.tolist())),
          test_mae=dict(zip(METRICS,np.abs(chosen-y[c]).mean(axis=0).tolist())),
          test_rmse=dict(zip(METRICS,np.sqrt(((chosen-y[c])**2).mean(axis=0)).tolist())),
          last_value_test_mae=dict(zip(METRICS,np.abs(test_naive-y[c]).mean(axis=0).tolist())),
          test_target_minutes=[minutes[int(i+horizon)] for i in origins[c]],
          note='Holdout scores precede final refit. No calibrated probability/confidence interval.'))
    return final


def infer(artifact,rows):
    if len(rows)<LAGS:raise ValueError('Need six completed minute samples.')
    rows=rows[-LAGS:]
    if any(b.minute-a.minute!=1 for a,b in zip(rows,rows[1:])):raise ValueError('Recent measurements contain a gap.')
    x=np.array([[getattr(r,m) for m in METRICS] for r in rows]).reshape(-1)
    weights=np.array(artifact['weights']);z=(x-artifact['mean'])/artifact['scale']
    result={}
    for i,metric in enumerate(METRICS):
        selected=artifact['selected'][i]
        contributions=z*weights[1:,i] if selected=='ridge' else np.zeros(len(x))
        intercept=float(weights[0,i]) if selected=='ridge' else float(x[-3+i])
        raw=intercept+float(contributions.sum());value=max(0,raw)
        result[metric]=dict(value=value,method=selected,unit='km/h' if metric=='average_speed' else 'vehicles',
            explanation=dict(intercept=intercept,
                contributions=[dict(feature=f'{m}_lag_{LAGS-1-j}',value=float(contributions[j*3+k]))
                    for j in range(LAGS) for k,m in enumerate(METRICS)],
                nonnegative_adjustment=value-raw),
            test_mae=artifact['evaluation']['test_mae'][metric])
    return result
