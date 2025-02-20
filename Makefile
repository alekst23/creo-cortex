install:
	pip install -r requirements.txt

build:
	python admin/start_target_docker.py

run:
	streamlit run src/front/streamlit_simple.py