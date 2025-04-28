start-mongo:
	sh admin/start_mongo.sh

install: start-mongo
	pip install -r requirements.txt

build:
	sh admin/run_manager.sh

run-mcp:
	python src/server/mcp_server.py

run-client:
	streamlit run src/front/streamlit_simple.py