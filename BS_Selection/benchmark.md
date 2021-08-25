## Lidar Model
### Hyper Paramters :
*	drop_prob=0.2 and drop_prob_fc=0.2,
*	weight_decay=1e-4
*	Number of epoch = 5
*	Batch Size = 64
*	Learning Rate = 1e-3

### Versions
*	version_1 : NU Huskies based model
*	version_2 : Imperial based model
*	version_3 : Imperial based model with dropout
*	version_4 : NU Huskies based model with higher kernel size
*	version_6 : imperial model with batch norm before prerelu activation
*	version_7 : improved model of version_4 with batchnorm and prerelu
*	version_9 : inception model

### Inference
*	Increase in kernel size incresed accuracy : From v1 and v4
*	Residual connection have negligible effect : From v1,v2, and v4
*	It is written that batch norm should be before PReLu but in practice after it, performs better