param(
  [Parameter(Mandatory=$true)]
  [string]$Month
)

$env:PYTHONPATH="."
python src\etl_run.py $Month
python scripts\export_powerbi_datasets.py