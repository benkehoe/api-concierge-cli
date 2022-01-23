Currently, you need to run the following, it's not working when put in `requirements.txt`:
```
python -m pip install -t src git+https://github.com/benkehoe/api-concierge-lib-python.git
```
then run
```
sam build --cached && sam deploy -g
```
