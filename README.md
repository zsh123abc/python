# python 環境設定

1. 透過啟動虛擬環境的方式來跑python
- Windows10 -> cmd模式下，執行啟動`./venv/Script/activate.bat`，關閉的話則為`./venv/Script/deactivate.bat`
- MAC, Linux -> zsh, bash模式下，執行`source ./venv/bin/activate` 關閉的話則為`deactivate`

2. 執行`pip list`確認是否有在虛擬環境下看到安裝的套件，再請執行`pip install -r requirements.txt`進行local install

# python flask api 啟動

在虛擬環境模式下執行 python run.py

# python test 執行

在flask啟動後再執行 pytest run.py


