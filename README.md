
To run this project you will ned docker compose

run docker compose build --no-cache and then run docker compose up --build

use this curl command the hit the API and run a long runnining asynchronous task on the worker

curl http://localhost:8000/ex1 -H "Content-Type: application/json" --data '{"amount": 1, "x": 10, "y": 3}'

then go to the dashboard on http://localhost:5556 to see stats of the proccesses 
