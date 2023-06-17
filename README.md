# cc-method-context

## models used
InCoder:
https://huggingface.co/facebook/incoder-1B

UniXcoder
https://huggingface.co/microsoft/unixcoder-base

CodeGPT
https://huggingface.co/AISE-TUDelft/CodeGPT-Multilingual

## dataset 
Dataset can be downloaded at
https://doi.org/10.5281/zenodo.8050981


## running entire experiment
Extract functions from the dataset folder
```shell
cd find-function-calls
npm i
npm run analyze -- <dataset_folder> <analysis_output_folder>
```

Create the test set
```shell
python3 create_test_set.py -i <analysis_output_folder> -o <output_file_path> -m 5 -p 1
```

Generate the predictions
```shell
python models/run_models -i <output_file_path> -o <output_dir_no_signatures> -m incoder unixcoder codegpt
python models/run_models -i <output_file_path> -o <output_dir_signatures> -m incoder unixcoder codegpt -s
```

Evaluate the predictions
```shell
python evaluate_models.py -is <output_dir_signatures> -in <output_dir_no_signatures>
```

## running with our output
Evaluate the predictions
```shell
python evaluate_models.py -is output/signatures -in output/no-signatures
```